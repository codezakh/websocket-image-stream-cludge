#!/usr/bin/env python
import os
from threading import Lock
from flask import Flask, render_template, session, request, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

import itertools

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()


frame_source_thread = None
frame_source_lock = Lock()

def frame_ordering(framename):
    *_, number_slug = framename.split('frame')
    frame_seq_number, _ = number_slug.split('.')
    return int(frame_seq_number)


def frame_source_background_thread():
    count = 0
    frame_files = os.listdir('./static/frames')
    cycler = itertools.cycle(
        sorted(
            [os.path.join('./static/frames', frame) for frame in frame_files],
            key=frame_ordering
        )
    ) 
    for frame in cycler:
        socketio.sleep(0.1)
        socketio.emit('new_frame', {'data': frame}, namespace='/test')
    # while True:
    #     socketio.sleep(10)
    #     count += 1
    #     socketio.emit('new_frame',
    #                   {'data': 'YEEEEEET', 'count': count},
    #                   namespace='/test')


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(10)
        count += 1
        socketio.emit('my_response',
                      {'data': 'Server generated event', 'count': count},
                      namespace='/test')

class FrameCycler:
    def __init__(self):
        self.frame_dir = './static/frames'

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@app.route('/frames')
def frame_view():
    return render_template('frames.html', async_mode=socketio.async_mode)

# @app.route('/frames')
# def frames():
#     frame_dir = './static/frames'
#     frames_in_dir = os.listdir(frame_dir)
#     return str(len(frames_in_dir))


@socketio.on('my_event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('my_broadcast_event', namespace='/test')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.on('join', namespace='/test')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('leave', namespace='/test')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close_room', namespace='/test')
def close(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         room=message['room'])
    close_room(message['room'])


@socketio.on('my_room_event', namespace='/test')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         room=message['room'])


@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()


@socketio.on('my_ping', namespace='/test')
def ping_pong():
    emit('my_pong')


@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    global frame_source_thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)
    with frame_source_lock:
        if frame_source_thread is None:
            frame_source_thread = socketio.start_background_task(target=frame_source_background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    socketio.run(app, debug=True)
