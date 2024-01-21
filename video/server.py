import json
import requests
import os
import traceback
import cv2
import logging
from capture import VideoCapture
from flask import Flask
from flask_socketio import SocketIO, emit
from threading import Thread
from time import sleep

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

server_url = f'{os.environ["SERVER_URL"]}:5555'

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', path='/video')

frame_cap = VideoCapture(0, width=960, height=720, exposure=0.06)


def run_threaded(job_func, *args, **kwargs):
    job_thread = Thread(target=job_func, args=args, kwargs=kwargs)
    job_thread.start()


def send_frames():
    while(True):
        img = frame_cap.read_cropped()

        try:
            response = requests.post(
                f'{server_url}/img',
                data=img.tobytes(),
                headers = {'content-type': 'image/jpeg'},
                verify=False
            )
            if response.content != b'':
                j = json.loads(response.text)

                print(j)
                socketio.emit('user_data', j)
            else:
                socketio.emit('user_data', None)
        
        except requests.exceptions.ConnectionError:
            print('Server not online')

        
        except Exception:
            print(traceback.format_exc())


@socketio.on('connect')
def connect():
    print('Client connected')
    emit('my response', {'data': 'Connected'})


@socketio.on('disconnect')
def disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    run_threaded(send_frames)
    socketio.run(app, debug=True, host='0.0.0.0', port=7000, use_reloader=False)