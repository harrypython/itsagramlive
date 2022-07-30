![GitHub](https://img.shields.io/github/license/harrypython/itsagramlive)
![PyPI](https://img.shields.io/pypi/v/itsagramlive)
![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/harrypython/itsagramlive?label=Version)

# It's A Gram Live

It's A Gram Live that creates an Instagram Live through a Python script. It provides you with an RTMP server and a stream key for streaming using software like [OBS-Studio](https://obsproject.com/) or [XSplit Broadcaster](https://www.xsplit.com/).

## Installation

```bash
pip install ItsAGramLive
```

## Usage

```python
from ItsAGramLive import ItsAGramLive

live = ItsAGramLive()

# or if you want to pre-define the username and password without args
# live = ItsAGramLive(
#    username='foo',
#    password='bar'
# )

live.start()
```

```bash
python3 live_broadcast.py -u yourInstagramUsername -p yourPassword -proxy user:password@ip:port
```

The output will give you the RTMP Server address and the Stream key (automatically copied to your clipboard)

###  Usage with FFMPEG
Note: It is not possible to use commands like ```chat``` or ```wave``` with this script.
The live will end when the file finishes streaming.
```python  
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
                         "-f flv '{stream_server}{stream_key}'".format(
						                       file=args.file,
                                                                       stream_server=live.stream_server,
                                                                       stream_key=live.stream_key
                                                                       )  
  
            print('CTRL+C to quit.')  
            try:  
                subprocess.call(ffmpeg_cmd, shell=True)  
            except KeyboardInterrupt:  
                pass  
            except Exception as error:  
                print(error)  
                live.end_broadcast()  
  
            live.end_broadcast()
```

```bash
python3 live_broadcast_ffmpeg.py -u yourInstagramUsername -p yourPassword -f /path/to/video/file.mp4
```
  
## Commands

- **info**
  Show details about the broadcast
- **mute comments**
  Prevent viewers from commenting
- **unmute comments**
  Allow viewers do comments
- **viewers**
  List viewers
- **chat**
  Send a comment
- **pin**
  Send a comment and pin it
- **unpin**
  Remove a pinned comment
- **comments**
  Get the list of comments
- **wave**
  Wave to a viewer
- **stop**
  Terminate broadcast

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[ GNU GPLv3 ](https://choosealicense.com/licenses/gpl-3.0/)

## Buy me a coffee

<a href="https://www.buymeacoffee.com/harrypython" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" style="height: 37px !important;" ></a>

## Instagram Bot
Check my Instagram Bot: [BurbnBot](https://github.com/harrypython/BurbnBot)
