<a href="https://github.com/harrypython/itsagramlive/blob/master/LICENSE">
    <img src="https://img.shields.io/badge/license-GPLv3-blue.svg" />
</a>
<a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/built%20with-Python3-red.svg" />
</a>

# It's A Gram Live

It's A Gram Live is a Python script that create a Instagram Live and provide you a rtmp server and stream key to streaming using sofwares like OBS-Studio.

## Installation

```bash
pip install ItsAGramLive
```
## Usage

```python
from ItsAGramLive import ItsAGramLive

live = ItsAGramLive()

broadcast_id = live.create_broadcast()

live.start_broadcast(broadcast_id)

live.end_broadcast(broadcast_id)
```

```bash
python3 live_broadcast.py -u yourInstagramUsername -p yourPassword -proxy user:password@ip:port -share True
```

The output will give you the RTMP Server address and the Stream key (automatically copied to your clipboard)

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[ GNU GPLv3 ](https://choosealicense.com/licenses/gpl-3.0/)


<a href="https://www.buymeacoffee.com/harrypython" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" style="height: 37px !important;" ></a>