import argparse
import hashlib
import hmac
import json
import time
import urllib
import uuid

import pyperclip
import requests

from .http import ClientCookieJar

import urllib.request as compat_urllib_request

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
    is_running: bool = False
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
    broadcast_id: int = None
    stream_key: str = None
    stream_server: str = None
    ad_id: str = None
    session_id: str = None

    opener = None
    DEVICE_SETS = {
        "app_version": "136.0.0.34.124",
        "android_version": "28",
        "android_release": "9.0",
        "dpi": "640dpi",
        "resolution": "1440x2560",
        "manufacturer": "samsung",
        "device": "SM-G965F",
        "model": "star2qltecs",
        "cpu": "samsungexynos9810",
        "version_code": "208061712",
    }

    API_URL = 'https://i.instagram.com/api/v1/'

    USER_AGENT = 'Instagram {app_version} Android ({android_version}/{android_release}; {dpi}; {resolution}; ' \
                 '{manufacturer}; {model}; armani; {cpu}; en_US)'.format(**DEVICE_SETS)
    IG_SIG_KEY = '4f8732eb9ba7d1c8e8897a75d6474d4eb3f5279137431b2aafb71fafe2abe178'
    SIG_KEY_VERSION = '4'

    def __init__(self, username='', password=''):

        if bool(username) == False and bool(password) == False:
            parser = argparse.ArgumentParser(add_help=True)
            parser.add_argument("-u", "--username", type=str, help="username", required=True)
            parser.add_argument("-p", "--password", type=str, help="password", required=True)
            parser.add_argument("-proxy", type=str, help="Proxy format - user:password@ip:port", default=None)
            args = parser.parse_args()

            username = args.username
            password = args.password

        m = hashlib.md5()
        m.update(username.encode('utf-8') + password.encode('utf-8'))
        self.device_id = self.generate_device_id(m.hexdigest())

        self.set_user(username=username, password=password)

        # App session id
        self.session_id = self.generate_UUID()
        self.ad_id = self.generate_adid()

        handlers = []

        # Handle Cookies
        cookie_string = None
        cookie_jar = ClientCookieJar(cookie_string=cookie_string)

        # Check Cookies expiration time
        if cookie_string and cookie_jar.auth_expires and int(time.time()) >= cookie_jar.auth_expires:
            raise Exception('Cookie expired at {0!s}'.format(cookie_jar.auth_expires))

        cookie_handler = compat_urllib_request.HTTPCookieProcessor(cookie_jar)

        handlers.extend([
            compat_urllib_request.HTTPHandler(),
            cookie_handler])

        opener = compat_urllib_request.build_opener(*handlers)
        opener.cookie_jar = cookie_jar
        self.opener = opener

    @property
    def settings(self):
        """Helper property that extracts the settings that you should cache
        in addition to username and password."""
        return {
            'uuid': self.uuid,
            'device_id': self.device_id,
            'ad_id': self.ad_id,
            'session_id': self.session_id,
            'cookie': self.cookie_jar.dump(),
            'created_ts': int(time.time())
        }


    @property
    def cookie_jar(self):
        """The client's cookiejar instance."""
        return self.opener.cookie_jar

    def set_user(self, username, password):
        self.username = username
        self.password = password
        self.uuid = self.generate_UUID(True)

    def generate_UUID(self, t: bool = True, seed=None):

        if seed:
            m = hashlib.md5()
            m.update(seed.encode('utf-8'))
            new_uuid = uuid.UUID(m.hexdigest())

            return str(new_uuid)
        else:
            generated_uuid = str(uuid.uuid1()) # change from uuid 4 to 1 for better use cases
            if t:
                return generated_uuid
            else:
                return generated_uuid.replace('-', '')

    def generate_device_id(self, seed):
        volatile_seed = "12345"
        m = hashlib.md5()
        m.update(seed.encode('utf-8') + volatile_seed.encode('utf-8'))
        return 'android-' + m.hexdigest()[:16]

    def generate_adid(self, seed=None):
        """
        Generate an Advertising ID based on the login username since
        the Google Ad ID is a personally identifying but resettable ID.
        """

        modified_seed = seed or self.username
        if modified_seed:
            # Do some trivial mangling of original seed
            sha2 = hashlib.sha256()
            sha2.update(modified_seed.encode('utf-8'))
            modified_seed = sha2.hexdigest()
        return self.generate_UUID(seed=modified_seed)

    def set_code_challenge_required(self, path, code):
        data = {'security_code': code,
                '_uuid': self.uuid,
                'guid': self.uuid,
                'device_id': self.device_id,
                '_uid': self.username_id,
                '_csrftoken': self.LastResponse.cookies['csrftoken']}

        self.send_request(path, self.generate_signature(json.dumps(data)), True)

    def get_code_challenge_required(self, path, choice=0):
        data = {'choice': choice,
                '_uuid': self.uuid,
                'guid': self.uuid,
                'device_id': self.device_id,
                '_uid': self.username_id,
                '_csrftoken': self.LastResponse.cookies['csrftoken']}

        self.send_request(path, self.generate_signature(json.dumps(data)), True)

    def login(self, force=False):
        if not self.isLoggedIn or force:
            if self.send_request(endpoint='si/fetch_headers/?challenge_type=signup&guid=' + self.generate_UUID(False),
                                 login=True):

                data = {'phone_id': self.generate_UUID(True),
                        '_csrftoken': self.LastResponse.cookies['csrftoken'],
                        'username': self.username,
                        'guid': self.uuid,
                        'device_id': self.device_id,
                        'password': self.password,
                        'login_attempt_count': '0'}

                if self.send_request('accounts/login/', post=self.generate_signature(json.dumps(data)), login=True):
                    if "two_factor_required" not in self.LastJson:
                        self.isLoggedIn = True
                        self.username_id = self.LastJson["logged_in_user"]["pk"]
                        self.rank_token = "%s_%s" % (self.username_id, self.uuid)
                        self.token = self.LastResponse.cookies["csrftoken"]
                        return True
                    else:
                        if self.two_factor():
                            self.isLoggedIn = True
                            self.username_id = self.LastJson["logged_in_user"]["pk"]
                            self.rank_token = "%s_%s" % (self.username_id, self.uuid)
                            self.token = self.LastResponse.cookies["csrftoken"]
                            return True

        return False

    def two_factor(self):
        # verification_method': 0 works for sms and TOTP. why? ¯\_ಠ_ಠ_/¯
        verification_code = input('Enter verification code: ')
        data = {
            'verification_method': 0,
            'verification_code': verification_code,
            'trust_this_device': 0,
            'two_factor_identifier': self.LastJson['two_factor_info']['two_factor_identifier'],
            '_csrftoken': self.LastResponse.cookies['csrftoken'],
            'username': self.username,
            'device_id': self.device_id,
            'guid': self.uuid,
        }
        if self.send_request('accounts/two_factor_login/', self.generate_signature(json.dumps(data)), login=True):
            return True
        else:
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
                    self.LastResponse = self.s.post(self.API_URL + endpoint, data=post, verify=verify)
                else:
                    self.LastResponse = self.s.get(self.API_URL + endpoint, verify=verify)

                self.LastJson = json.loads(self.LastResponse.text)

                break
            except Exception as e:
                print('* Except on SendRequest (wait 60 sec and resend): {}'.format(str(e)))
                time.sleep(60)

        if self.LastResponse.status_code == 200:
            return True
        elif 'two_factor_required' in self.LastJson and self.LastResponse.status_code == 400:
            # even the status code isn't 200 return True if the 2FA is required
            if self.LastJson['two_factor_required']:
                print("Two factor required")
                return True
        elif 'message' in self.LastJson and self.LastResponse.status_code == 400:
            if self.LastJson['message'] == 'challenge_required':
                path = self.LastJson['challenge']['api_path'][1:]
                choice = int(input('Choose a challenge mode (0 - SMS, 1 - Email): '))
                self.get_code_challenge_required(path, choice)
                code = input('Enter the code: ')
                self.set_code_challenge_required(path, code)
        else:
            error_message = " - "
            if "message" in self.LastJson:
                error_message = self.LastJson['message']
            print('* ERROR({}): {}'.format(self.LastResponse.status_code, error_message))
            print(self.LastResponse)
            return False

    def set_proxy(self, proxy=None):
        if proxy is not None:
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
        print("Let's do it!")
        if self.login():
            print("You'r logged in")

            if self.create_broadcast():
                print("Broadcast ID: {}")
                print("* Broadcast ID: {}".format(self.broadcast_id))
                print("* Server URL: {}".format(self.stream_server))
                print("* Server Key: {}".format(self.stream_key))
                print("The stream key was automatically copied to your clipboard")

                print("Press Enter after your setting your streaming software.")
                if self.start_broadcast():
                    self.is_running = True

                    while self.is_running:
                        cmd = input('command> ')

                        if cmd == "stop":
                            self.stop()

                        elif cmd == "mute comments":
                            self.mute_comments()

                        elif cmd == "unmute comments":
                            self.unmute_comment()

                        elif cmd == 'info':
                            self.live_info()

                        elif cmd == 'viewers':
                            users, ids = self.get_viewer_list()
                            print(users)

                        elif cmd == 'comments':
                            self.get_comments()

                        elif cmd[:4] == 'chat':
                            to_send = cmd[5:]
                            if to_send:
                                self.send_comment(to_send)
                            else:
                                print('usage: chat <text to chat>')

                        elif cmd == 'wave':
                            users, ids = self.get_viewer_list()
                            for i in range(len(users)):
                                print(f'{i + 1}. {users[i]}')
                            print('Type number according to user e.g 1.')
                            while True:
                                cmd = input('number> ')

                                if cmd == 'back':
                                    break
                                try:
                                    user_id = int(cmd) - 1
                                    self.wave(ids[user_id])
                                    break
                                except:
                                    print('Please type number e.g 1')

                        else:
                            print(
                                'Available commands:\n\t '
                                '"stop"\n\t '
                                '"mute comments"\n\t '
                                '"unmute comments"\n\t '
                                '"info"\n\t '
                                '"viewers"\n\t '
                                '"comments"\n\t '
                                '"chat"\n\t '
                                '"wave"\n\t')

    def get_viewer_list(self):
        if self.send_request("live/{}/get_viewer_list/".format(self.broadcast_id)):
            users = []
            ids = []
            for user in self.LastJson['users']:
                users.append(f"{user['username']}")
                ids.append(f"{user['pk']}")

            return users, ids

    def wave(self, user_id):
        data = json.dumps(
            {'_uid': self.username_id, '_uuid': self.uuid, '_csrftoken': self.token, 'viewer_id': user_id})

        if self.send_request('live/{}/wave/'.format(self.broadcast_id), post=self.generate_signature(data)):
            return True
        return False

    def live_info(self):
        if self.send_request("live/{}/info/".format(self.broadcast_id)):
            viewer_count = self.LastJson['viewer_count']

            print("[*]Broadcast ID: {}".format(self.broadcast_id))
            print("[*]Server URL: {}".format(self.stream_server))
            print("[*]Stream Key: {}".format(self.stream_key))
            print("[*]Viewer Count: {}".format(viewer_count))
            print("[*]Status: {}".format(self.LastJson['broadcast_status']))

    def mute_comments(self):
        data = json.dumps({'_uuid': self.uuid, '_uid': self.username_id, '_csrftoken': self.token})
        if self.send_request(endpoint='live/{}/mute_comment/'.format(self.broadcast_id),
                             post=self.generate_signature(data)):
            print("Comments muted")
            return True

        return False

    def unmute_comment(self):
        data = json.dumps({'_uuid': self.uuid, '_uid': self.username_id, '_csrftoken': self.token})
        if self.send_request(endpoint='live/{}/unmute_comment/'.format(self.broadcast_id),
                             post=self.generate_signature(data)):
            print("Comments un-muted")
            return True

        return False

    def send_comment(self, msg):
        data = json.dumps({
            'idempotence_token': self.generate_UUID(True),
            'comment_text': msg,
            'live_or_vod': 1,
            'offset_to_video_start': 0
        })

        if self.send_request("live/{}/comment/".format(self.broadcast_id), post=self.generate_signature(data)):
            if self.LastJson['status'] == 'ok':
                return True

    def create_broadcast(self):
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
            self.broadcast_id = last_json['broadcast_id']

            upload_url = last_json['upload_url'].split(str(self.broadcast_id))

            self.stream_server = upload_url[0]
            self.stream_key = "{}{}".format(str(self.broadcast_id), upload_url[1])

            pyperclip.copy(self.stream_key)

            return True

        else:

            return False

    def start_broadcast(self):
        data = json.dumps({'_uuid': self.uuid,
                           '_uid': self.username_id,
                           'should_send_notifications': 1,
                           '_csrftoken': self.token})

        if self.send_request(endpoint='live/' + str(self.broadcast_id) + '/start/', post=self.generate_signature(data)):
            return True
        else:
            return False

    def end_broadcast(self):
        data = json.dumps({'_uuid': self.uuid, '_uid': self.username_id, '_csrftoken': self.token})
        if self.send_request(endpoint='live/' + str(self.broadcast_id) + '/end_broadcast/',
                             post=self.generate_signature(data)):
            return True
        return False

    def add_to_post_live(self):
        data = json.dumps({'_uuid': self.uuid, '_uid': self.username_id, '_csrftoken': self.token})
        if self.send_request(endpoint='live/{}/add_to_post_live/'.format(self.broadcast_id),
                             post=self.generate_signature(data)):
            print('Live Posted to Story!')
            return True
        return False

    def delete_post_live(self):
        data = json.dumps({'_uuid': self.uuid, '_uid': self.username_id, '_csrftoken': self.token})
        if self.send_request(endpoint='live/{}/delete_post_live/'.format(self.broadcast_id),
                             post=self.generate_signature(data)):
            return True
        return False

    def stop(self):
        self.end_broadcast()
        print('Save Live replay to story ? <y/n>')
        save = input('command> ')
        if save == 'y':
            self.add_to_post_live()
        else:
            self.delete_post_live()
        print('Exiting...')
        self.is_running = False
        print('Bye bye')

    def get_comments(self):
        if self.send_request("live/{}/get_comment/".format(self.broadcast_id)):
            if 'comments' in self.LastJson:
                for comment in self.LastJson['comments']:
                    print(f"{comment['user']['username']} has posted a new comment: {comment['text']}")
            else:
                print("There is no comments.")
