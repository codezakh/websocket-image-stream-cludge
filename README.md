Adapted from Miguel Grinberg's Flask-SocketIO example.

This repo demonstrates how you can use websockets to render a series
of successive images as a hacked together streaming video player.

```
# tested on 3.5.6
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# opencv installation may fail, thats fine - it isn't needed for the app to run
cd example
python app.py
```
