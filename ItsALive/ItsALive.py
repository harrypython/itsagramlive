import argparse
import json
import time

import pyperclip
from instabot import Bot
from progress.spinner import Spinner


class ItsALive:
    bot = Bot()
    previewWidth: int = 1080
    previewHeight: int = 1920
    broadcastMessage: str = ""
    sendNotification: bool = True
    add_to_post_live: bool = True
    last_comment_ts: int = 1

    def __init__(self):
        parser = argparse.ArgumentParser(add_help=True)
        parser.add_argument("-u", type=str, help="username")
        parser.add_argument("-p", type=str, help="password")
        args = parser.parse_args()

        self.bot.login(username=args.u, password=args.p)

    def create_broadcast(self):
        data = json.dumps({'_uuid': self.bot.api.uuid,
                           '_uid': self.bot.api.user_id,
                           'preview_height': self.previewHeight,
                           'preview_width': self.previewWidth,
                           'broadcast_message': self.broadcastMessage,
                           'broadcast_type': 'RTMP',
                           'internal_only': 0,
                           '_csrftoken': self.bot.api.token})

        if self.bot.api.send_request('live/create/', data, login=False, headers={"X-DEVICE-ID": self.bot.api.uuid}):
            last_json = self.bot.api.last_json
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

        return broadcast_id

    def start_broadcast(self, broadcast_id):
        data = json.dumps({'_uuid': self.bot.api.uuid,
                           '_uid': self.bot.api.user_id,
                           'should_send_notifications': int(self.sendNotification),
                           '_csrftoken': self.bot.api.token})

        if self.bot.api.send_request('live/' + str(broadcast_id) + '/start/', data, login=False,
                                     headers={"X-DEVICE-ID": self.bot.api.uuid}):

            print('CTRL+C to quit.')
            spinner = Spinner(" - ")
            try:
                while True:
                    spinner.next()
                    self.get_last_comment(broadcast_id)
            except KeyboardInterrupt:
                spinner.finish()
                pass
            except Exception as error:
                print(error)
                breakpoint()
                self.end_broadcast(broadcast_id)

    def end_broadcast(self, broadcast_id):
        data = json.dumps({'_uuid': self.bot.api.uuid, '_uid': self.bot.api.user_id, '_csrftoken': self.bot.api.token})
        if self.bot.api.send_request('live/' + str(broadcast_id) + '/end_broadcast/', data, login=False,
                                     headers={"X-DEVICE-ID": self.bot.api.uuid}):
            if self.add_to_post_live:
                self.bot.api.send_request('live/' + str(broadcast_id) + '/add_to_post_live/', data, login=False,
                                          headers={"X-DEVICE-ID": self.bot.api.uuid})

        print('Ending Broadcasting')

    def get_comments(self, broadcast_id):
        data = json.dumps({'_uuid': self.bot.api.uuid, '_uid': self.bot.api.user_id, '_csrftoken': self.bot.api.token})
        endpoint = "live/{}/get_comment/?last_comment_ts={}".format(str(broadcast_id), str(self.last_comment_ts))

        if self.bot.api.send_request(endpoint, data, login=False, headers={"X-DEVICE-ID": self.bot.api.uuid}):
            last_json = self.bot.api.last_json
            breakpoint()
        else:
            breakpoint()
