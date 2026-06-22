ARG PYTHON_IMAGE=python:3.14-slim-bookworm

FROM ${PYTHON_IMAGE} AS python-base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ARG APP_UID=10001
ARG APP_GID=10001

WORKDIR /app

RUN groupadd --gid "${APP_GID}" app \
    && useradd --uid "${APP_UID}" --gid "${APP_GID}" --create-home --shell /usr/sbin/nologin app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY backend ./backend
COPY frontend ./frontend
COPY migrations ./migrations
COPY prompts ./prompts

RUN mkdir -p /app/.data/uploads \
    && chown -R app:app /app

USER app:app

FROM python-base AS api

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python-base AS frontend

EXPOSE 8501
CMD ["streamlit", "run", "frontend/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false"]

FROM ${PYTHON_IMAGE} AS whisper-builder

ARG WHISPER_CPP_VERSION=v1.9.1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates cmake git build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch "${WHISPER_CPP_VERSION}" https://github.com/ggerganov/whisper.cpp.git /tmp/whisper.cpp \
    && cmake -S /tmp/whisper.cpp -B /tmp/whisper-build \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_SHARED_LIBS=OFF \
        -DWHISPER_BUILD_TESTS=OFF \
        -DWHISPER_BUILD_EXAMPLES=ON \
    && cmake --build /tmp/whisper-build --target whisper-cli --config Release \
    && cp /tmp/whisper-build/bin/whisper-cli /tmp/whisper-cli

FROM python-base AS worker

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
COPY --from=whisper-builder /tmp/whisper-cli /usr/local/bin/whisper-cli
RUN chmod 0755 /usr/local/bin/whisper-cli \
    && chown app:app /usr/local/bin/whisper-cli

ENV FFMPEG_EXECUTABLE=/usr/bin/ffmpeg
ENV WHISPER_CPP_EXECUTABLE=/usr/local/bin/whisper-cli

USER app:app
CMD ["rq", "worker", "media-processing", "--url", "redis://redis:6379/0"]
