FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends libgmp-dev libmpfr-dev libmpc-dev \
    && rm -rf /var/lib/apt/lists/*
