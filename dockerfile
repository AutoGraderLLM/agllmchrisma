# Use a generic Linux-x64 image (Ubuntu 22.04)
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV RUNNER_VERSION=2.323.0
ENV RUNNER_ARCH=x64
ENV GH_RUNNER_TOKEN=""
ENV GH_RUNNER_REPO_URL=""
ENV GH_RUNNER_NAME="teacher-llm-runner"
ENV GH_RUNNER_LABELS="self-hosted,docker"

# NEW: make Ollama listen on all interfaces
ENV OLLAMA_HOST=0.0.0.0:11434

# System deps + tooling
RUN apt-get update && apt-get install -y \
    bc curl git jq build-essential libssl-dev libffi-dev \
    python3 python3-pip python3-venv cmake ninja-build sqlite3 \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# ─── Ollama CLI ───────────────────────────────────────────────
RUN curl -fsSL https://ollama.com/install.sh | sh
# ──────────────────────────────────────────────────────────────

# GitHub Actions runner & app prep
RUN mkdir -p /actions-runner /app
WORKDIR /actions-runner
RUN curl -fsSL -o actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz \
      https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz \
 && tar xzf actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz \
 && rm -f actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz \
 && mv run.sh runner.sh

WORKDIR /app
COPY requirements.txt /app/
RUN python3 -m pip install --upgrade pip \
 && python3 -m pip install --no-cache-dir -r requirements.txt
COPY . /app/

WORKDIR /actions-runner
COPY run.sh .
RUN chmod +x run.sh

RUN useradd -ms /bin/bash runner \
 && chown -R runner:runner /actions-runner /app /home/runner
USER runner

# Expose Ollama (11434) and your teacher-UI port (5003)
EXPOSE 11434 5003

################################################################
# ENTRYPOINT: start daemon → wait → pull model → run runner
################################################################
ENTRYPOINT ["sh","-c", "\
export OLLAMA_HOST=${OLLAMA_HOST}; \
ollama serve & \
until curl -sf http://localhost:11434/api/tags >/dev/null; do \
  echo 'Waiting for Ollama daemon…'; sleep 2; \
done; \
ollama pull qwen2.5-coder && exec /actions-runner/run.sh \
"]
