FROM ubuntu:21.04

WORKDIR /opt

RUN apt update && DEBIAN_FRONTEND=noninteractive apt install -y \
    alsa-base \
    git \
    libatlas-base-dev \
    libffi-dev \
    libssl-dev \
    locales \
    portaudio19-dev \
    pulseaudio \
    python3 \
    python3-pip \
    sox \
    swig

# set locale and timezone
RUN locale-gen en_GB.UTF-8
ENV LANG en_GB.UTF-8
ENV LANGUAGE en_GB:en
ENV LC_ALL en_GB.UTF-8

ENV TZ=Europe/Rome
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone


# install snowboy from source
RUN git clone --depth 1 https://github.com/pmec-home/snowboy-aarch64 snowboy && \
    cd snowboy && \
    python3 setup.py build && \
    python3 setup.py bdist_wheel && \
    pip3 install dist/snowboy*.whl && \
    cd .. && rm -rf snowboy

# install python dependencies
RUN pip3 install --upgrade setuptools
RUN pip3 install --upgrade pip

COPY ./src/requirements.txt requirements.txt
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
RUN pip3 install -r requirements.txt --no-cache-dir

# patch google sdk not working with python 3.9
RUN sed -i 's/arr.tostring()/arr.tobytes()/g' \
    /usr/local/lib/python3.9/dist-packages/googlesamples/assistant/grpc/audio_helpers.py