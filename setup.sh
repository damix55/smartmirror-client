#!/bin/bash

# Add Chromium repo
sudo add-apt-repository -y ppa:saiarcot895/chromium-beta
sudo apt update -y

# Install needed packages
sudo apt install -y --no-install-recommends \
    linux-modules-extra-raspi \
    xserver-xorg \
    xserver-xorg-video-fbdev \
    x11-xserver-utils \
    xinit \
    matchbox \
    chromium-browser

# Install docker + docker-compose
curl -s https://get.docker.com | bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.2.2/docker-compose-linux-aarch64" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose
sudo usermod -aG docker $USER && newgrp docker

# Generate and mount swap
if ! grep -q '/swapfile' /etc/fstab ; then
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile swap swap defaults 0 0' | sudo tee -a  /etc/fstab
fi

# Start X automatically on boot
chmod +x ~/client/kiosk_mode.sh
echo '[[ -z $DISPLAY && $XDG_VTNR -eq 1 ]] && sudo xinit ~/client/kiosk_mode.sh -- -nocursor' >> ~/.bash_profile
