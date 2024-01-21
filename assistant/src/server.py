# Copyright (C) 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Sample that implements a gRPC client for the Google Assistant API."""

import json
import logging
import os
import os.path
import pathlib2 as pathlib
import sys
import time
import uuid
import queue
import subprocess
import threading
import requests

import click
import grpc
import google.auth.transport.grpc
import google.auth.transport.requests
import google.oauth2.credentials

from google.assistant.embedded.v1alpha2 import (
    embedded_assistant_pb2,
    embedded_assistant_pb2_grpc
)

from googlesamples.assistant.grpc import assistant_helpers

from tenacity import retry, stop_after_attempt, retry_if_exception

from voice_engine.source import Source
from voice_engine.kws import KWS

from gen_audio_conf import generate_audio_configuration

from flask import Flask, request
from flask_socketio import SocketIO

from difflib import SequenceMatcher

from recorder import Recorder

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', path='/assistant')

audio_capture = Recorder()

ASSISTANT_API_ENDPOINT = 'embeddedassistant.googleapis.com'
END_OF_UTTERANCE = embedded_assistant_pb2.AssistResponse.END_OF_UTTERANCE
DIALOG_FOLLOW_ON = embedded_assistant_pb2.DialogStateOut.DIALOG_FOLLOW_ON
CLOSE_MICROPHONE = embedded_assistant_pb2.DialogStateOut.CLOSE_MICROPHONE
PLAYING = embedded_assistant_pb2.ScreenOutConfig.PLAYING
DEFAULT_GRPC_DEADLINE = 60 * 3 + 5
SERVER_URL = f'{os.environ["SERVER_URL"]}:5555'


class Player(object):
    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.aplay = None

    def start_playback(self):
        cmd = [
            'aplay',
            '-f', 'S16_LE',
            '-r', str(self.sample_rate),
            '-c', str(self.channels),
            '-'
        ]
        self.aplay = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def put(self, data):
        if self.is_playing():
            self.thread = threading.Thread(target=self.aplay.stdin.write, args=(data,))
            self.thread.start()
            

    def stop_playback(self):
        try:
            self.aplay.stdin.close()
        except AttributeError:
            pass

    def is_playing(self):
        return  self.aplay and (self.aplay.poll() is None)



class SampleAssistant(object):
    """Sample Assistant that supports conversations and device actions.

    Args:
      device_model_id: identifier of the device model.
      device_id: identifier of the registered device instance.
      conversation_stream(ConversationStream): audio stream
        for recording query and playing back assistant answer.
      channel: authorized gRPC channel for connection to the
        Google Assistant API.
      deadline_sec: gRPC deadline in seconds for Google Assistant API call.
      device_handler: callback for device actions.
    """

    def __init__(self, language_code, device_model_id, device_id,
                 channel, deadline_sec):
        self.language_code = language_code
        self.device_model_id = device_model_id
        self.device_id = device_id
        self.sample_rate = 16000
        self.volume_percentage = 100

        # Opaque blob provided in AssistResponse that,
        # when provided in a follow-up AssistRequest,
        # gives the Assistant a context marker within the current state
        # of the multi-Assist()-RPC "conversation".
        # This value, along with MicrophoneMode, supports a more natural
        # "conversation" with the Assistant.
        self.conversation_state = None
        # Force reset of first conversation.
        self.is_new_conversation = True

        # Create Google Assistant API gRPC client.
        self.assistant = embedded_assistant_pb2_grpc.EmbeddedAssistantStub(
            channel
        )
        self.deadline = deadline_sec

        self.player = Player()
        self.playing = False

        self.listening = False
        self.audio_queue = queue.Queue()

        self.volume_percentage = 100

        self.done = False
        self.listening_event = threading.Event()
        self.thread = None

        self.text_query = None
        self.custom_skill_query = None


    def listen(self):
        time.sleep(0.7)
        self.listening_event.set()

    def run(self):
        continue_conversation = False
        while not self.done:
            if not continue_conversation:
                self.listening_event.wait()
                self.listening_event.clear()

                if self.done:
                    break

            for a in self.assist():
                socketio.emit(*a)

                if a[0] == 'continue_conversation':
                    continue_conversation = a[1]


    def start(self):
        self.done = False
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.done = True
        self.listening_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)

    def put(self, data):
        if self.listening:
            self.audio_queue.put(data)

    def __enter__(self):
        return self

    def __exit__(self, etype, e, traceback):
        if e:
            return False


    def assist(self):
        """Send a voice request to the Assistant and playback the response.

        Returns: True if conversation should continue.
        """
        continue_conversation = False
        transcript = ''
        is_custom_skill = self.custom_skill_query is not None

        self.audio_queue.queue.clear()

        if not is_custom_skill:
            self.listening = True
            logging.info('Recording audio request.')
            yield ('assistant_state', 'listening')

        def iter_log_assist_requests():
            for c in self.gen_assist_requests():
                yield c
            logging.debug('Reached end of AssistRequest iteration.')

        # This generator yields AssistResponse proto messages
        # received from the gRPC Google Assistant API.
        for resp in self.assistant.Assist(iter_log_assist_requests(),
                                          self.deadline):
            if resp.event_type == END_OF_UTTERANCE:
                if audio_capture.recording:
                    audio_capture.stop_and_save()
                    files = {'utterance': open('tmp/utterance.wav','rb'), 'keyword': open('tmp/keyword.wav','rb')}

                    try:
                        voice_analysis = requests.post(f'{SERVER_URL}/voice_analysis', files=files)
                        print(voice_analysis.json())
                        yield ('voice_analysis', voice_analysis.json())
                    except:
                        print('Server error')


                logging.info('End of audio request detected.')
                yield ('assistant_state', 'thinking')
                logging.info('Stopping recording.')
                self.listening = False

                # Resoconto giornaliero
                day_overview_confidence = SequenceMatcher(None, transcript[-21:],'resoconto giornaliero').ratio()
                if day_overview_confidence > 0.85:
                    logging.info(f'Activating day overview skill (confidence: {day_overview_confidence})')
                    self.text_query='parla con smart mirror'
                    self.custom_skill_query='resoconto giornaliero'
                    yield ('continue_conversation', False)
                    self.is_new_conversation = True
                    self.listening_event.set()
                    return self.assist()

                # Regista utente *name*
                registration_activation_confidence = SequenceMatcher(None, transcript[:15],'registra utente').ratio()
                if registration_activation_confidence > 0.85:
                    logging.info(f'Activating registration skill (confidence: {registration_activation_confidence})')
                    self.text_query='parla con smart mirror'
                    self.custom_skill_query=transcript
                    yield ('continue_conversation', False)
                    self.is_new_conversation = True
                    self.listening_event.set()
                    return self.assist()

                # Avvia registrazione
                # registration_activation_confidence = SequenceMatcher(None, transcript,'avvia registrazione').ratio()
                # if registration_activation_confidence > 0.85:
                #     logging.info(f'Activating registration skill (confidence: {registration_activation_confidence})')
                #     self.text_query='parla con smart mirror'
                #     self.custom_skill_query='avvia registrazione'
                #     yield ('continue_conversation', False)
                #     self.is_new_conversation = True
                #     self.listening_event.set()
                #     return self.assist()
                    


            if resp.speech_results:
                transcript = ' '.join(r.transcript for r in resp.speech_results)
                yield ('transcript', transcript)
                logging.info('Transcript of user request: "%s".', transcript)

            if len(resp.audio_out.audio_data) > 0 and not is_custom_skill:
                if not self.player.is_playing():
                    self.listening = False
                    self.player.start_playback()
                    # self.conversation_stream.start_playback()
                    yield ('assistant_state', 'speaking')
                    logging.info('Playing assistant response.')
                # self.conversation_stream.write(resp.audio_out.audio_data)
                if resp.screen_out.data:
                    yield ('graphic_response', resp.screen_out.data.decode())
                self.player.put(resp.audio_out.audio_data)

            if resp.screen_out.data:
                yield ('graphic_response', resp.screen_out.data.decode())

            if resp.dialog_state_out.conversation_state:
                conversation_state = resp.dialog_state_out.conversation_state
                logging.debug('Updating conversation state.')
                self.conversation_state = conversation_state

            if resp.dialog_state_out.volume_percentage != 0:
                volume_percentage = resp.dialog_state_out.volume_percentage
                logging.info('Setting volume to %s%%', volume_percentage)
                self.volume_percentage = volume_percentage

            if resp.dialog_state_out.microphone_mode == DIALOG_FOLLOW_ON:
                continue_conversation = True
                logging.info('Expecting follow-on query from user.')
                if is_custom_skill:
                    self.text_query=self.custom_skill_query
                    self.custom_skill_query=None

            elif resp.dialog_state_out.microphone_mode == CLOSE_MICROPHONE:
                continue_conversation = False
                if is_custom_skill:
                    self.text_query=None
                    self.custom_skill_query=None

            if resp.device_action.device_request_json:
                device_request = json.loads(
                    resp.device_action.device_request_json
                )
                print(device_request)
                # fs = self.device_handler(device_request)
                # if fs:
                #     device_actions_futures.extend(fs)



        # if len(device_actions_futures):
        #     logging.info('Waiting for device executions to complete.')
        #     concurrent.futures.wait(device_actions_futures)

        logging.info('Finished playing assistant response.')
        self.player.stop_playback()

        time.sleep(2)
        if not continue_conversation:
            yield ('assistant_state', 'idle')
            
        yield ('continue_conversation', continue_conversation)

    def gen_assist_requests(self):
        """Yields: AssistRequest messages to send to the API."""

        config = embedded_assistant_pb2.AssistConfig(
            audio_in_config=embedded_assistant_pb2.AudioInConfig(
                encoding='LINEAR16',
                sample_rate_hertz=self.sample_rate,
            ),
            audio_out_config=embedded_assistant_pb2.AudioOutConfig(
                encoding='LINEAR16',
                sample_rate_hertz=self.sample_rate,
                volume_percentage=self.volume_percentage,
            ),
            dialog_state_in=embedded_assistant_pb2.DialogStateIn(
                language_code=self.language_code,
                conversation_state=self.conversation_state,
                is_new_conversation=self.is_new_conversation,
            ),
            device_config=embedded_assistant_pb2.DeviceConfig(
                device_id=self.device_id,
                device_model_id=self.device_model_id,
            ),
            text_query=self.text_query
        )

        config.screen_out_config.screen_mode = PLAYING
        # Continue current conversation with later requests.
        self.is_new_conversation = False
        # The first AssistRequest must contain the AssistConfig
        # and no audio data.
        req = embedded_assistant_pb2.AssistRequest(config=config)
        yield req

        if self.text_query is None:
            while self.listening:
                try:
                    data = self.audio_queue.get(timeout=1)
                except queue.Empty:
                    # print('no data available')
                    break
                # Subsequent requests need audio data, but not config.
                yield embedded_assistant_pb2.AssistRequest(audio_in=data)

        else:
            self.text_query = None
            assistant_helpers.log_assist_request_without_audio(req)

        


@click.command()
@click.option('--api-endpoint', default=ASSISTANT_API_ENDPOINT,
              metavar='<api endpoint>', show_default=True,
              help='Address of Google Assistant API service.')
@click.option('--credentials',
              metavar='<credentials>', show_default=True,
              default=os.path.join(click.get_app_dir('google-oauthlib-tool'),
                                   'credentials.json'),
              help='Path to read OAuth2 credentials.')
@click.option('--project-id',
              metavar='<project id>',
              help=('Google Developer Project ID used for registration '
                    'if --device-id is not specified'))
@click.option('--device-model-id',
              metavar='<device model id>',
              help=(('Unique device model identifier, '
                     'if not specifed, it is read from --device-config')))
@click.option('--device-id',
              metavar='<device id>',
              help=(('Unique registered device instance identifier, '
                     'if not specified, it is read from --device-config, '
                     'if no device_config found: a new device is registered '
                     'using a unique id and a new device config is saved')))
@click.option('--device-config', show_default=True,
              metavar='<device config>',
              default=os.path.join(
                  click.get_app_dir('googlesamples-assistant'),
                  'device_config.json'),
              help='Path to save and restore the device configuration')
@click.option('--lang', show_default=True,
              metavar='<language code>',
              default='it-IT',
              help='Language code of the Assistant')
@click.option('--verbose', '-v', is_flag=True, default=False,
              help='Verbose logging.')
@click.option('--grpc-deadline', default=DEFAULT_GRPC_DEADLINE,
              metavar='<grpc deadline>', show_default=True,
              help='gRPC deadline in seconds')
@click.option('--once', default=False, is_flag=True,
              help='Force termination after a single conversation.')
def main(api_endpoint, credentials, project_id,
         device_model_id, device_id, device_config,
         lang, verbose, grpc_deadline, once, *args, **kwargs):
    """Samples for the Google Assistant API.

    Examples:
      Run the sample with microphone input and speaker output:

        $ python -m googlesamples.assistant

      Run the sample with file input and speaker output:

        $ python -m googlesamples.assistant -i <input file>

      Run the sample with file input and output:

        $ python -m googlesamples.assistant -i <input file> -o <output file>
    """
    # Setup logging.
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    # Load OAuth 2.0 credentials.
    try:
        with open(credentials, 'r') as f:
            credentials = google.oauth2.credentials.Credentials(token=None,
                                                                **json.load(f))
            http_request = google.auth.transport.requests.Request()
            credentials.refresh(http_request)
    except Exception as e:
        logging.error('Error loading credentials: %s', e)
        logging.error('Run google-oauthlib-tool to initialize '
                      'new OAuth 2.0 credentials.')
        sys.exit(-1)

    # Create an authorized gRPC channel.
    grpc_channel = google.auth.transport.grpc.secure_authorized_channel(
        credentials, http_request, api_endpoint)
    logging.info('Connecting to %s', api_endpoint)


    if not device_id or not device_model_id:
        try:
            with open(device_config) as f:
                device = json.load(f)
                device_id = device['id']
                device_model_id = device['model_id']
                logging.info("Using device model %s and device id %s",
                             device_model_id,
                             device_id)
        except Exception as e:
            logging.warning('Device config not found: %s' % e)
            logging.info('Registering device')
            if not device_model_id:
                logging.error('Option --device-model-id required '
                              'when registering a device instance.')
                sys.exit(-1)
            if not project_id:
                logging.error('Option --project-id required '
                              'when registering a device instance.')
                sys.exit(-1)
            device_base_url = (
                'https://%s/v1alpha2/projects/%s/devices' % (api_endpoint,
                                                             project_id)
            )
            device_id = str(uuid.uuid1())
            payload = {
                'id': device_id,
                'model_id': device_model_id,
                'client_type': 'SDK_SERVICE'
            }
            session = google.auth.transport.requests.AuthorizedSession(
                credentials
            )
            r = session.post(device_base_url, data=json.dumps(payload))
            if r.status_code != 200:
                logging.error('Failed to register device: %s', r.text)
                sys.exit(-1)
            logging.info('Device registered: %s', device_id)
            pathlib.Path(os.path.dirname(device_config)).mkdir(exist_ok=True)
            with open(device_config, 'w') as f:
                json.dump(payload, f)

    

    assistant = SampleAssistant(lang, device_model_id, device_id,
                         grpc_channel, grpc_deadline)

    src = Source(rate=16000, frames_size=1600)
    kws = KWS(model='smart_mirror', sensitivity=0.6)

    src.link(kws)
    src.link(audio_capture)
    kws.link(assistant)

    def on_keyword(keyword):
        if not audio_capture.recording:
            print('listening')
            audio_capture.start()
            assistant.listen()

        print('detected')
    


    kws.on_detected = on_keyword

    assistant.start()
    kws.start()
    src.start()

    socketio.run(app, debug=True, host='0.0.0.0', port=5000, use_reloader=False)

    src.stop()
    kws.stop()
    assistant.stop()
            

if __name__ == '__main__':
    print('Generating audio configuration')
    generate_audio_configuration()

    print('Setting volume to 100%')
    os.popen('amixer set Headphone 100%')
    
    main()
