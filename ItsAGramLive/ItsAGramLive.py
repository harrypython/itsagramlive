import argparse
import json

import pyperclip
from InstagramAPI import InstagramAPI
from progress.spinner import Spinner


class ItsAGramLive:
    ig: InstagramAPI = None
    previewWidth: int = 1080
    previewHeight: int = 1920
    broadcastMessage: str = ""
    sendNotification: bool = True
    share_to_story: bool = False
    last_comment_ts: int = 1

    def __init__(self):
        parser = argparse.ArgumentParser(add_help=True)
        parser.add_argument("-u", "--username", type=str, help="username", required=True)
        parser.add_argument("-p", "--password", type=str, help="password", required=True)
        parser.add_argument("-share", type=bool, help="Share to Story after ended", default=self.share_to_story)
        parser.add_argument("-proxy", type=str, help="Proxy format - user:password@ip:port", default=None)
        args = parser.parse_args()

        self.share_to_story = args.share
        self.ig = InstagramAPI(username=args.username, password=args.password)

        self.ig.setProxy(proxy=args.proxy)

    def create_broadcast(self):
        if self.ig.login():
            data = json.dumps({'_uuid': self.ig.uuid,
                               '_uid': self.ig.username_id,
                               'preview_height': self.previewHeight,
                               'preview_width': self.previewWidth,
                               'broadcast_message': self.broadcastMessage,
                               'broadcast_type': 'RTMP',
                               'internal_only': 0,
                               '_csrftoken': self.ig.token})

            if self.ig.SendRequest(endpoint='live/create/', post=self.ig.generateSignature(data)):
                last_json = self.ig.LastJson
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
        data = json.dumps({'_uuid': self.ig.uuid,
                           '_uid': self.ig.username_id,
                           'should_send_notifications': int(self.sendNotification),
                           '_csrftoken': self.ig.token})

        if self.ig.SendRequest(endpoint='live/' + str(broadcast_id) + '/start/', post=self.ig.generateSignature(data)):

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
        data = json.dumps({'_uuid': self.ig.uuid, '_uid': self.ig.username_id, '_csrftoken': self.ig.token})
        if self.ig.SendRequest(endpoint='live/' + str(broadcast_id) + '/end_broadcast/',
                               post=self.ig.generateSignature(data)):
            if self.share_to_story:
                self.ig.SendRequest(endpoint='live/' + str(broadcast_id) + '/add_to_post_live/',
                                    post=self.ig.generateSignature(data))

        print('Ending Broadcasting')
