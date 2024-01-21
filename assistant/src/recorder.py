import pyaudio
import wave
import os

class Recorder(pyaudio.PyAudio):
    def __init__(self, *args, **kwargs):
        super(pyaudio.PyAudio, self).__init__(*args, **kwargs)
        self.recording = False
        self.record = []

    def put(self, data):
        # every frame in record is 0.1 seconds, so 10 frames are 1 second
        if not self.recording and len(self.record)==10:
            self.record.pop(0)
        self.record.append(data)

        if len(self.record)==200:   # timeout: 20s
            self.stop()

    def save(self):
        os.makedirs('tmp', exist_ok=True)
        f = wave.open('tmp/utterance.wav','w')
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        for data in self.record:
            f.writeframesraw(data)
        f.close()

        f = wave.open('tmp/keyword.wav','w')
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        for data in self.record[:15]:
            f.writeframesraw(data)
        f.close()

    def start(self):
        self.recording = True

    def stop_and_save(self):
        self.save()
        self.stop()

    def stop(self):
        self.recording = False
        self.record = []