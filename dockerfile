# Use a generic Linux-x64 image (Ubuntu 22.04)
FROM ubuntu:22.04

# Set non-interactive mode for apt-get.
ENV DEBIAN_FRONTEND=noninteractive

# Set environment variables for the GitHub Actions runner.
# (Sensitive values should be supplied at runtime.)
ENV RUNNER_VERSION=2.323.0
ENV RUNNER_ARCH=x64
ENV GH_RUNNER_TOKEN=""
ENV GH_RUNNER_REPO_URL=""
ENV GH_RUNNER_NAME="teacher-llm-runner"
ENV GH_RUNNER_LABELS="self-hosted,docker"

# Update package lists and install required packages:
# - Runner tools: curl, git, jq
# - Build tools: build-essential, libssl-dev, libffi-dev, python3-dev
# - Python and pip
# - Tools for building llama-cpp-python: cmake, ninja-build, sqlite3
RUN apt-get update && apt-get install -y \
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

# Create directories for the GitHub Actions runner and your application code.
RUN mkdir /actions-runner && mkdir /app

# Set up the GitHub Actions runner.
WORKDIR /actions-runner
RUN curl -o actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz -L \
    https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz \
    && tar xzf actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz \
    && rm -f actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz \
    && mv run.sh runner.sh

# Switch to /app and copy your application code.
WORKDIR /app
COPY requirements.txt /app/
RUN python3 -m pip install --upgrade pip && python3 -m pip install --no-cache-dir -r requirements.txt
COPY . /app/

# Copy your custom startup script (run.sh) into the runner directory.
WORKDIR /actions-runner
COPY run.sh .
RUN chmod +x run.sh

# Create a non-root user "runner" and change ownership of the directories.
RUN useradd -ms /bin/bash runner && \
    chown -R runner:runner /app /actions-runner

# Switch to the non-root user.
USER runner

# Expose port 5003 for your teacher UI.
EXPOSE 5003

# Use the run.sh script as the container's entrypoint.
ENTRYPOINT ["/actions-runner/run.sh"]
