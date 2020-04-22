import argparse
import hashlib
import hmac
import json
import time
import urllib
import uuid

import pyperclip
import requests
from progress.spinner import Spinner
# Turn off InsecureRequestWarning
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class ItsAGramLive:
    previewWidth: int = 1080
    previewHeight: int = 1920
    broadcastMessage: str = ""
    sendNotification: bool = True
    share_to_story: bool = False
    last_comment_ts: int = 1
    username: str = None
    password: str = None
    username_id: str = None
    rank_token: str = None
    token: str = None
    uuid: str = None
    LastJson: dict = None
    LastResponse = None
    s = requests.Session()
    isLoggedIn: bool = False

    API_URL = 'https://i.instagram.com/api/v1/'
    DEVICE_SETS = {'manufacturer': 'Xiaomi',
                   'model': 'HM 1SW',
                   'android_version': 18,
                   'android_release': '4.3'}
    USER_AGENT = 'Instagram 10.26.0 Android ({android_version}/{android_release}; 320dpi; 720x1280; {manufacturer}; {model}; armani; qcom; en_US)'.format(
        **DEVICE_SETS)
    IG_SIG_KEY = '4f8732eb9ba7d1c8e8897a75d6474d4eb3f5279137431b2aafb71fafe2abe178'
    SIG_KEY_VERSION = '4'

    def __init__(self):
        parser = argparse.ArgumentParser(add_help=True)
        parser.add_argument("-u", "--username", type=str, help="username", required=True)
        parser.add_argument("-p", "--password", type=str, help="password", required=True)
        parser.add_argument("-share", type=bool, help="Share to Story after ended", default=self.share_to_story)
        parser.add_argument("-proxy", type=str, help="Proxy format - user:password@ip:port", default=None)
        args = parser.parse_args()

        m = hashlib.md5()
        m.update(args.username.encode('utf-8') + args.password.encode('utf-8'))
        self.device_id = self.generate_device_id(m.hexdigest())

        self.set_user(username=args.username, password=args.password)

        self.share_to_story = args.share

    def set_user(self, username, password):
        self.username = username
        self.password = password
        self.uuid = self.generate_UUID(True)

    def generate_UUID(self, t: bool = True):
        generated_uuid = str(uuid.uuid4())
        if t:
            return generated_uuid
        else:
            return generated_uuid.replace('-', '')

    def generate_device_id(self, seed):
        volatile_seed = "12345"
        m = hashlib.md5()
        m.update(seed.encode('utf-8') + volatile_seed.encode('utf-8'))
        return 'android-' + m.hexdigest()[:16]

    def login(self, force=False):
        if not self.isLoggedIn or force:
            if self.send_request('si/fetch_headers/?challenge_type=signup&guid=' + self.generate_UUID(False), None,
                                 True):

                data = {'phone_id': self.generate_UUID(True),
                        '_csrftoken': self.LastResponse.cookies['csrftoken'],
                        'username': self.username,
                        'guid': self.uuid,
                        'device_id': self.device_id,
                        'password': self.password,
                        'login_attempt_count': '0'}

                if self.send_request('accounts/login/', self.generate_signature(json.dumps(data)), True):
                    self.isLoggedIn = True
                    self.username_id = self.LastJson["logged_in_user"]["pk"]
                    self.rank_token = "%s_%s" % (self.username_id, self.uuid)
                    self.token = self.LastResponse.cookies["csrftoken"]

                    print("Login success!\n")
                    return True
        return False

    def send_request(self, endpoint, post=None, login=False):
        verify = False  # don't show request warning

        if not self.isLoggedIn and not login:
            raise Exception("Not logged in!\n")

        self.s.headers.update({'Connection': 'close',
                               'Accept': '*/*',
                               'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                               'Cookie2': '$Version=1',
                               'Accept-Language': 'en-US',
                               'User-Agent': self.USER_AGENT})

        while True:
            try:
                if post is not None:
                    response = self.s.post(self.API_URL + endpoint, data=post, verify=verify)
                else:
                    response = self.s.get(self.API_URL + endpoint, verify=verify)
                break
            except Exception as e:
                print('Except on SendRequest (wait 60 sec and resend): ' + str(e))
                time.sleep(60)

        if response.status_code == 200:
            self.LastResponse = response
            self.LastJson = json.loads(response.text)
            return True
        else:
            print("Request return " + str(response.status_code) + " error!")
            # for debugging
            try:
                self.LastResponse = response
                self.LastJson = json.loads(response.text)
                print(self.LastJson)
            except:
                pass
            return False

    def set_proxy(self, proxy=None):
        """
        Set proxy for all requests::

        Proxy format - user:password@ip:port
        """

        if proxy is not None:
            print('Set proxy!')
            proxies = {'http': 'http://' + proxy, 'https': 'http://' + proxy}
            self.s.proxies.update(proxies)

    def generate_signature(self, data, skip_quote=False):
        if not skip_quote:
            try:
                parsed_data = urllib.parse.quote(data)
            except AttributeError:
                parsed_data = urllib.quote(data)
        else:
            parsed_data = data
        return 'ig_sig_key_version=' + self.SIG_KEY_VERSION + '&signed_body=' + hmac.new(
            self.IG_SIG_KEY.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest() + '.' + parsed_data

    def start(self):
        broadcast = self.create_broadcast()

        self.start_broadcast(broadcast_id=broadcast)

        self.end_broadcast(broadcast_id=broadcast)

    def create_broadcast(self):
        if self.login():
            data = json.dumps({'_uuid': self.uuid,
                               '_uid': self.username_id,
                               'preview_height': self.previewHeight,
                               'preview_width': self.previewWidth,
                               'broadcast_message': self.broadcastMessage,
                               'broadcast_type': 'RTMP',
                               'internal_only': 0,
                               '_csrftoken': self.token})

            if self.send_request(endpoint='live/create/', post=self.generate_signature(data)):
                last_json = self.LastJson
                broadcast_id = last_json['broadcast_id']
                upload_url = last_json['upload_url']

                splited = upload_url.split(str(broadcast_id))

                stream_key = "{}{}".format(str(broadcast_id), splited[1])

                server = splited[0]

                print("Server: {}".format(server))
                pyperclip.copy(stream_key)
                print("Stream Key (copied to clipboard): {}".format(stream_key))

            else:
                return False

        else:
            return False

        return broadcast_id

    def start_broadcast(self, broadcast_id):
        data = json.dumps({'_uuid': self.uuid,
                           '_uid': self.username_id,
                           'should_send_notifications': int(self.sendNotification),
                           '_csrftoken': self.token})

        if self.send_request(endpoint='live/' + str(broadcast_id) + '/start/', post=self.generate_signature(data)):

            print('CTRL+C to quit.')
            spinner = Spinner(" - ")
            try:
                while True:
                    spinner.next()
            except KeyboardInterrupt:
                spinner.finish()
                pass
            except Exception as error:
                print(error)
                self.end_broadcast(broadcast_id)

    def end_broadcast(self, broadcast_id):
        data = json.dumps({'_uuid': self.uuid, '_uid': self.username_id, '_csrftoken': self.token})
        if self.send_request(endpoint='live/' + str(broadcast_id) + '/end_broadcast/',
                             post=self.generate_signature(data)):
            if self.share_to_story:
                self.send_request(endpoint='live/' + str(broadcast_id) + '/add_to_post_live/',
                                  post=self.generate_signature(data))

        print('Ending Broadcasting')
