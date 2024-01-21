# SmartMirror Client

## Hardware used
- Raspberry Pi 3 Model B+
- FullHD monitor connected over HDMI (mounted vertically)
- ELP 720p USB Camera with built-in microphone
- Speaker connected over the 3.5mm jack

## Installation on Raspberry
* Install [Ubuntu 21.10 Server](https://cdimage.ubuntu.com/releases/21.10/release/ubuntu-21.10-preinstalled-server-arm64+raspi.img.xz) on an SD card
* On the partition `system-boot` of the SD card:
    * Add the flag `display_rotate=3` to `config.txt` (to rotate the video output)
    * Set up network connection in `network-config`
    * Enable SSH by running `touch ssh` (to create an empty file named `ssh`)
* Insert the SD card in the Raspberry Pi and start the OS
* Once it's started, connect in SSH (default credentials are: user `ubuntu` with password `ubuntu`)

## How to run
* Clone this repo in ~/client: `cd && git clone https://gitlab.com/damix55/sm-client.git client`
* Run `setup.sh` (installs Raspberry dependencies)
* Add `client_secret.json` and `device_config.json` in `./assistant/config`
* Start the containers with `docker-compose up`

## Authorize Google Assistant
To authorize Google Assistant run `docker exec -it assistant bash -c './auth.sh'`. It will provide an URL to visit, where you can log in with your Google Account. After logging in, copy the code provided and paste it in the terminal where you ran the last command. After the authorization process, restart the `assistant` container.

## Autologin at startup (Raspberry)
Run `sudo systemctl edit getty@tty1.service` and add:

```bash
[Service]
ExecStart=
ExecStart=-/sbin/agetty --noissue --autologin ubuntu %I $TERM
Type=idle
```