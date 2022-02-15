import argparse
import hashlib
import hmac
import json
import os
import time
import urllib
import uuid
import tempfile
import pyperclip
import requests
import logging
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
    pinned_comment_id: str = None
    basic_headers: dict = {}

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

    def __init__(self, username='', password='', logging_level='INFO'):
        logging.basicConfig(level=logging_level)
        logging.getLogger("urllib3").setLevel(logging_level)

        if bool(username) is False and bool(password) is False:
            parser = argparse.ArgumentParser(add_help=True)
            parser.add_argument("-u", "--username", type=str, help="username", required=True)
            parser.add_argument("-p", "--password", type=str, help="password", required=True)
            parser.add_argument("-proxy", type=str, help="Proxy format - user:password@ip:port", default=None)
            try:
                args = parser.parse_args()
            except SystemExit:
                logging.fatal('Error while parsing arguments. Did you provide your Username & Password ?')
                raise Exception('Credentials not provided')

            username = args.username
            password = args.password

        m = hashlib.md5()
        m.update(username.encode('utf-8') + password.encode('utf-8'))
        self.device_id = self.generate_device_id(m.hexdigest())

        self.set_user(username=username, password=password)

        self.basic_headers = {
            'Connection': 'close',
            'Accept': '*/*',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept-Encoding': 'gzip, deflate',
            'Cookie2': '$Version=1',
            'Accept-Language': 'en-US',
            'User-Agent': self.USER_AGENT,
        }


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
        logging.info('Logging in.')
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
                    if "error_type" in self.LastJson:
                        if self.LastJson['error_type'] == 'bad_password':
                            logging.error(self.LastJson['message'])
                            return False

                    if "two_factor_required" not in self.LastJson:
                        self.isLoggedIn = True
                        self.username_id = self.LastJson["logged_in_user"]["pk"]
                        self.rank_token = "%s_%s" % (self.username_id, self.uuid)
                        self.token = self.LastResponse.cookies["csrftoken"]
                        logging.info('Logged in.')
                        return True
                    else:
                        if self.two_factor():
                            self.isLoggedIn = True
                            self.username_id = self.LastJson["logged_in_user"]["pk"]
                            self.rank_token = "%s_%s" % (self.username_id, self.uuid)
                            self.token = self.LastResponse.cookies["csrftoken"]
                            logging.info('Logged in.')
                            return True
        raise Exception("bad_password")

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

    def send_request(self, endpoint, post=None, login=False, headers: dict = {}):
        verify = False  # don't show request warning

        if not self.isLoggedIn and not login:
            raise Exception("Not logged in!\n")

        h = self.basic_headers
        h.update(headers)

        self.s.headers.update(h)

        while True:
            try:
                if post is not None:
                    self.LastResponse = self.s.post(self.API_URL + endpoint, data=post, verify=verify)
                else:
                    self.LastResponse = self.s.get(self.API_URL + endpoint, verify=verify)

                self.LastJson = json.loads(self.LastResponse.text)

                break
            except Exception as e:
                logging.warning('* Except on SendRequest (wait 60 sec and resend): {}'.format(str(e)))
                time.sleep(60)

        if self.LastResponse.status_code == 200:
            return True
        elif 'two_factor_required' in self.LastJson and self.LastResponse.status_code == 400:
            # even the status code isn't 200 return True if the 2FA is required
            if self.LastJson['two_factor_required']:
                logging.info("Two factor required")
                return True
        elif 'message' in self.LastJson and self.LastResponse.status_code == 400 and self.LastJson['message'] == 'challenge_required':
            path = self.LastJson['challenge']['api_path'][1:]
            # choice = int(input('Choose a challenge mode (0 - SMS, 1 - Email): '))
            self.get_code_challenge_required(path, 1)
            raise Exception("challenge_required")
            # code = input('Enter the code: ')
            # self.set_code_challenge_required(path, code)
            # if message is 'Pre-allocated media not Found.'
        else:
            error_message = " - "
            if "message" in self.LastJson:
                error_message = self.LastJson['message']
            logging.error('* ERROR({}): {}'.format(self.LastResponse.status_code, error_message))
            logging.error(self.LastResponse)
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
        logging.info("Starting, let's do it !")
        if not self.login():
            logging.error("Error {}".format(self.LastResponse.status_code))
            logging.error(json.loads(self.LastResponse.text).get("message"))
        else:
            logging.info("You're logged in.")

            if self.create_broadcast():
                logging.info("Broadcast ID: {}")
                logging.info("* Broadcast ID: {}".format(self.broadcast_id))
                logging.info("* Server URL: {}".format(self.stream_server))
                logging.info("* Server Key: {}".format(self.stream_key))

                try:
                    pyperclip.copy(self.stream_key)
                    logging.info("The stream key was automatically copied to your clipboard")
                except pyperclip.PyperclipException as headless_error:
                    logging.error("Could not find a copy/paste mechanism for your system")
                    pass

                logging.info("Press Enter after your setting your streaming software.")

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
                            logging.info(users)

                        elif cmd == 'comments':
                            self.get_comments()

                        elif cmd[:3] == 'pin':
                            to_send = cmd[4:]
                            if to_send:
                                self.pin_comment(to_send)
                            else:
                                logging.info('usage: chat <text to chat>')

                        elif cmd[:5] == 'unpin':
                            self.unpin_comment()

                        elif cmd[:4] == 'chat':
                            to_send = cmd[5:]
                            if to_send:
                                self.send_comment(to_send)
                            else:
                                logging.info('usage: chat <text to chat>')

                        elif cmd == 'wave':
                            users, ids = self.get_viewer_list()
                            for i in range(len(users)):
                                logging.info(f'{i + 1}. {users[i]}')
                            logging.info('Type number according to user e.g 1.')
                            while True:
                                cmd = input('number> ')

                                if cmd == 'back':
                                    break
                                try:
                                    user_id = int(cmd) - 1
                                    self.wave(ids[user_id])
                                    break
                                except:
                                    logging.error('Please type number e.g 1')

                        else:
                            logging.info(
                                'Available commands:\n\t '
                                '"stop"\n\t '
                                '"mute comments"\n\t '
                                '"unmute comments"\n\t '
                                '"info"\n\t '
                                '"viewers"\n\t '
                                '"comments"\n\t '
                                '"chat"\n\t '
                                '"pin"\n\t '
                                '"unpin"\n\t '
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

            logging.info("[*]Broadcast ID: {}".format(self.broadcast_id))
            logging.info("[*]Server URL: {}".format(self.stream_server))
            logging.info("[*]Stream Key: {}".format(self.stream_key))
            logging.info("[*]Viewer Count: {}".format(viewer_count))
            logging.info("[*]Status: {}".format(self.LastJson['broadcast_status']))

    def mute_comments(self):
        data = json.dumps({'_uuid': self.uuid, '_uid': self.username_id, '_csrftoken': self.token})
        if self.send_request(endpoint='live/{}/mute_comment/'.format(self.broadcast_id),
                             post=self.generate_signature(data)):
            logging.info("Comments muted")
            return True

        return False

    def unmute_comment(self):
        data = json.dumps({'_uuid': self.uuid, '_uid': self.username_id, '_csrftoken': self.token})
        if self.send_request(endpoint='live/{}/unmute_comment/'.format(self.broadcast_id),
                             post=self.generate_signature(data)):
            logging.info("Comments un-muted")
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
        return False

    def create_broadcast(self):
        logging.info("Creating broadcast...")
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

            logging.info("Broadcast created.")
            return self

        else:
            logging.error("Error while creating broadcast.")
            return False

    def start_broadcast(self):
        logging.info("Starting broadcast...")
        data = json.dumps({'_uuid': self.uuid,
                           '_uid': self.username_id,
                           'should_send_notifications': 1,
                           '_csrftoken': self.token})

        if self.send_request(endpoint='live/' + str(self.broadcast_id) + '/start/', post=self.generate_signature(data)):
            logging.info("Broadcast started.")
            return True
        else:
            logging.error("Error while starting broadcast.")
            return False

    def end_broadcast(self):
        data = json.dumps({'_uuid': self.uuid, '_uid': self.username_id, '_csrftoken': self.token})
        if self.send_request(endpoint='live/' + str(self.broadcast_id) + '/end_broadcast/',
                             post=self.generate_signature(data)):
            return True
        return False

    def get_post_live_thumbnails(self):
        if self.send_request(endpoint="live/{}/get_post_live_thumbnails/".format(self.broadcast_id)):
            return self.LastJson.get("thumbnails")[int(len(self.LastJson.get("thumbnails")) / 2)]


    def add_post_live_to_igtv(self, description, title):
        self.end_broadcast()
        h = {
            'Priority': 'u=3',
            'User-Agent': self.USER_AGENT,
            'Accept-Language': 'en-US',
            'IG-U-DS-USER-ID': str(self.username_id),
            'IG-INTENDED-USER-ID': str(self.username_id),
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'i.instagram.com',
            'X-FB-HTTP-Engine': 'Liger',
            'X-FB-Client-IP': 'True',
            'X-FB-Server-Cluster': 'True',
            'Connection': 'close',

        }
        if self.send_request(endpoint='igtv/igtv_creation_tools', headers=h):
            data = json.dumps({
                "igtv_ads_toggled_on": "0",
                # "timezone_offset": "-28800",
                "_csrftoken": str(self.token),
                "source_type": "4",
                "_uid": str(self.username_id),
                "device_id": self.device_id,
                "keep_shoppable_products": "0",
                "_uuid": self.uuid,
                "title": title,
                "caption": description,
                "igtv_share_preview_to_feed": "1",
                "upload_id": self.upload_live_thumbnails(),
                "igtv_composer_session_id": self.generate_UUID(True),
                "device": {
                    "manufacturer": self.DEVICE_SETS["manufacturer"],
                    "model": self.DEVICE_SETS["model"],
                    "android_version": self.DEVICE_SETS["android_version"],
                    "android_release": self.DEVICE_SETS["android_release"]},
                "extra": {"source_width": 504, "source_height": 896}
            })

            h = {
                'X-IG-Device-ID': self.device_id,
                'is_igtv_video': '1',
                'retry_context': '{"num_reupload":0,"num_step_auto_retry":0,"num_step_manual_retry":0}',
                'Priority': 'u=3',
                'User-Agent': self.USER_AGENT,
                'IG-U-DS-USER-ID': str(self.username_id),
                'IG-INTENDED-USER-ID': str(self.username_id),
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Accept-Encoding': 'gzip, deflate',
                'Host': 'i.instagram.com',
                'X-FB-HTTP-Engine': 'Liger',
                'X-FB-Client-IP': 'True',
                'X-FB-Server-Cluster': 'True',
                'Connection': 'close',
            }

            if self.send_request(endpoint='media/configure_to_igtv/', post=self.generate_signature(data), headers=h):
                logging.info('Live Posted to Story!')
                return True
        return False

    def stop(self, save_to_igtv: bool = None, title = 'Live video', description = 'Live Instagram video.'):
        final_save = save_to_igtv

        if final_save is None:
            logging.info('Save Live replay to IGTV ? <y/n>')
            save_to_igtv = input('command> ')
            if save_to_igtv == 'y':
                final_save = 1
                title = input("Title: ")
                description = input("Description: ")
        
        if final_save:
            self.add_post_live_to_igtv(description, title)

        logging.info('Ending broadcast...')
        self.end_broadcast()
        self.is_running = False
        logging.info('Bye bye')

    def get_comments(self):
        if self.send_request("live/{}/get_comment/".format(self.broadcast_id)):
            if 'comments' in self.LastJson:
                for comment in self.LastJson['comments']:
                    logging.info(f"{comment['user']['username']} has posted a new comment: {comment['text']}")
            else:
                logging.info("There is no comments.")

    def pin_comment(self, to_send):
        if self.send_comment(msg=to_send):
            if self.send_request("live/{}/get_comment/".format(self.broadcast_id)):
                for comment in [comment for comment in self.LastJson['comments']]:
                    if comment.get("text") == to_send:
                        self.pinned_comment_id = comment.get("pk")
                data = json.dumps(
                    {
                        "_csrftoken": self.token,
                        "_uid": self.username_id,
                        "_uuid": self.uuid,
                        "comment_id": self.pinned_comment_id
                    })
                if self.send_request(endpoint='live/{}/pin_comment/'.format(self.broadcast_id),
                                     post=self.generate_signature(data)):
                    logging.info('Comment pinned!')
                    return True

        return False

    def unpin_comment(self):
        data = json.dumps({
            "_csrftoken": self.token,
            "_uid": self.username_id,
            "_uuid": self.uuid,
            "comment_id": self.pinned_comment_id
        })
        if self.send_request(endpoint='live/{}/unpin_comment/'.format(self.broadcast_id),
                             post=self.generate_signature(data)):
            logging.info('Comment unpinned!')
            return True
        return False
