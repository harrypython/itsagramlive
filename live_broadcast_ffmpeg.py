import argparse
import subprocess
from ItsAGramLive import ItsAGramLive

parser = argparse.ArgumentParser(add_help=True)
parser.add_argument("-u", "--username", type=str, help="username", required=True)
parser.add_argument("-p", "--password", type=str, help="password", required=True)
parser.add_argument("-f", "--file", type=str, help="File", required=True)
args = parser.parse_args()

live = ItsAGramLive(username=args.username, password=args.password)

if live.login():
    print("You'r logged in")

    if live.create_broadcast():

        if live.start_broadcast():
            ffmpeg_cmd = "ffmpeg " \
                         "-rtbufsize 256M " \
                         "-re " \
                         "-i '{file}' " \
                         "-acodec libmp3lame " \
                         "-ar 44100 " \
                         "-b:a 128k " \
                         "-pix_fmt yuv420p " \
                         "-profile:v baseline " \
                         "-s 720x1280 " \
                         "-bufsize 6000k " \
                         "-vb 400k " \
                         "-maxrate 1500k " \
                         "-deinterlace " \
                         "-vcodec libx264 " \
                         "-preset veryfast " \
                         "-g 30 -r 30 " \
                         "-f flv '{stream_server}{stream_key}'".format(file=args.file,
                                                                       stream_server=live.stream_server,
                                                                       stream_key=live.stream_key)

            print('CTRL+C to quit.')
            try:
                subprocess.call(ffmpeg_cmd, shell=True)
            except KeyboardInterrupt:
                pass
            except Exception as error:
                print(error)
                live.end_broadcast()

            live.end_broadcast()
