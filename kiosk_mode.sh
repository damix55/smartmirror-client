#!/bin/sh

xset -dpms                  # disable DPMS (Energy Star) features.
xset s off                  # disable screen saver
xset s noblank              # don't blank the video device

# Start matchbox
matchbox-window-manager &

# Start Chromium in kiosk mode
chromium-browser --no-sandbox --disable-infobars --noerrdialogs --kiosk 'http://localhost:3000'