FROM python:3.11.9-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    git \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libportaudio2 \
    portaudio19-dev \
    tesseract-ocr \
    tesseract-ocr-jpn \
    && rm -rf /var/lib/apt/lists/*

COPY setup/requirements.txt /tmp/build/requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install -r /tmp/build/requirements.txt \
    && python -m pip install "jax[cpu]==0.4.38" \
    && rm -rf /tmp/build /root/.cache/pip

WORKDIR /workspace/team-info
CMD ["python", "--version"]
