# Use a generic Linux-x64 image (Ubuntu 22.04)
FROM ubuntu:22.04

# Avoid any interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# GitHub Actions runner version and labels (provided at runtime via --env)
ENV RUNNER_VERSION=2.323.0
ENV RUNNER_ARCH=x64
ENV GH_RUNNER_TOKEN=""
ENV GH_RUNNER_REPO_URL=""
ENV GH_RUNNER_NAME="teacher-llm-runner"
ENV GH_RUNNER_LABELS="self-hosted,docker"

# Install system dependencies, including 'bc' for your hex tests,
# plus curl so we can fetch Ollama’s installer script
RUN apt-get update && apt-get install -y \
    bc \
    curl \
    git \
    jq \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3 \
    python3-pip \
    python3-venv \
    cmake \
    ninja-build \
    sqlite3 \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# ─── Install Ollama CLI ─────────────────────────────────────────────────────────
# This drops /usr/local/bin/ollama into the image.
RUN curl -fsSL https://ollama.com/install.sh | sh
# ────────────────────────────────────────────────────────────────────────────────

# Create directories for the runner and your app code
RUN mkdir -p /actions-runner /app

# Download and unpack the GitHub Actions runner
WORKDIR /actions-runner
RUN curl -fsSL \
      -o actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz \
      https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz \
    && tar xzf actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz \
    && rm -f actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz \
    && mv run.sh runner.sh

# Install your Python requirements and copy in all app files
WORKDIR /app
COPY requirements.txt /app/
RUN python3 -m pip install --upgrade pip \
 && python3 -m pip install --no-cache-dir -r requirements.txt
COPY . /app/

# Copy your custom run.sh into the runner directory
WORKDIR /actions-runner
COPY run.sh .
RUN chmod +x run.sh

# Ensure the runner user exists and owns everything
RUN useradd -ms /bin/bash runner \
 && chown -R runner:runner /actions-runner /app /home/runner

# Switch to the unprivileged runner user
USER runner

# Expose your teacher UI port
EXPOSE 5003

# ─── Entrypoint: pull the LLM, then launch the runner ─────────────────────────
# When the container starts, this will:
#  1) pull qwen2.5-coder:14b into Ollama’s local cache
#  2) hand off to your existing run.sh
ENTRYPOINT ["sh","-c","ollama pull qwen2.5-coder && exec /actions-runner/run.sh"]
# ────────────────────────────────────────────────────────────────────────────────
