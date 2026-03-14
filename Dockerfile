FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    python3-full \
    python3-pip \
    curl && \
    rm -rf /var/lib/apt/lists/*
    
RUN curl -fsSL https://opencode.ai/install | bash

# Install npm for docker
## Use bash for the shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

## Create a script file sourced by both interactive and non-interactive bash shells
ENV BASH_ENV /root/.bash_env
RUN touch "${BASH_ENV}"
RUN echo '. "${BASH_ENV}"' >> ~/.bashrc

## Download and install nvm
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | PROFILE="${BASH_ENV}" bash
RUN echo node > .nvmrc
RUN nvm install

RUN npm install -g @ramtinj95/opencode-tokenscope

COPY ./code/requirements.txt /tmp/requirements.txt

RUN python3 -m pip install --break-system-packages -r /tmp/requirements.txt
