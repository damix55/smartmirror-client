#!/bin/sh

google-oauthlib-tool --save --headless \
    --scope https://www.googleapis.com/auth/assistant-sdk-prototype \
    --client-secrets /root/client_secret.json