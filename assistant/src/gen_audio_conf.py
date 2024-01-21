import os
import re
import yaml

def generate_audio_configuration():
    with open("/root/audio.yml", "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    match = r'card (\d+): (.+) \[(.+)\], device (\d+): (.+) \[(.+)\]'

    # playback
    playback_device = ()

    playback_devices_raw = os.popen("aplay -l").read()
    playback_devices = re.findall(match, playback_devices_raw)

    for p in playback_devices:
        for playback_card_name in config['playback']:
            if p[4] == playback_card_name:
                playback_device = p
                break

    # capture
    capture_device = ()

    capture_devices_raw = os.popen("arecord -l").read()
    capture_devices = re.findall(match, capture_devices_raw)

    for p in capture_devices:
        for capture_card_name in config['capture']:
            if p[4] == capture_card_name:
                capture_device = p
                break


    asoundrc = f"""
        pcm.!default {{
        type asym
            playback.pcm {{
                type plug
                slave.pcm "hw:{playback_device[0]},{playback_device[3]}"
            }}
        capture.pcm {{
                type plug
                slave.pcm "hw:{capture_device[0]},{capture_device[3]}"
            }}
        }}

        ctl.!default {{
            type hw
            card 0
        }}
    """

    with open('/root/.asoundrc', 'w') as file:
        file.write(asoundrc)

if __name__ == '__main__':
    generate_audio_configuration()