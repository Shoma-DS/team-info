FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=UTC \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TEAM_INFO_ROOT=/workspace/team-info \
    PATH=/opt/team-info-venv/bin:${PATH}

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    ffmpeg \
    git \
    gnupg \
    python3 \
    python3-pip \
    python3-venv \
    tesseract-ocr \
    tesseract-ocr-jpn \
    tini \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc/apt/keyrings \
  && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
  && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
  && apt-get update \
  && apt-get install -y --no-install-recommends nodejs \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/team-info

COPY setup/requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/team-info-venv \
  && /opt/team-info-venv/bin/pip install --upgrade pip setuptools wheel \
  && /opt/team-info-venv/bin/pip install -r /tmp/requirements.txt

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["bash"]
