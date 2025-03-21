#!/bin/bash
set -e

#---------------------------
# One-Time Setup Section
#---------------------------
if [ ! -f /tmp/setup_done ]; then
    echo "Installing Rich library..."
    pip install --user rich || { echo "Failed to install Rich. Exiting."; exit 1; }

    # Change to /app for database setup.
    if [ -d "/app" ]; then
        cd /app
    else
        echo "/app directory not found! Exiting."
        exit 1
    fi

    echo "Running create_database.py..."
    python3 create_database.py || { echo "Error running create_database.py. Exiting."; exit 1; }

    echo "Running verify_db.py..."
    python3 verify_db.py || { echo "Error running verify_db.py. Exiting."; exit 1; }

    if [ -f "control_code.py" ]; then
        echo "Moving control_code.py to \$HOME..."
        mv control_code.py "$HOME" || { echo "Error moving control_code.py to \$HOME. Exiting."; exit 1; }
    else
        echo "control_code.py not found, skipping move."
    fi

    echo "Database setup completed successfully!"

    # Start the teacher UI.
    export TEACHER_UI_PORT=5003
    echo "Starting teacher UI in the background on port ${TEACHER_UI_PORT}..."
    cd /app
    python3 teacher_ui.py &
    UI_PID=$!
    echo $UI_PID > /tmp/ui_pid

    # Mark setup as done.
    touch /tmp/setup_done
else
    echo "Setup already completed, skipping one-time setup."
fi

#---------------------------
# Runner Configuration Section
#---------------------------
cd /actions-runner

echo "Removing previous runner configuration if it exists..."
./config.sh remove --token "${GH_RUNNER_TOKEN}" || echo "No previous runner configuration found."

echo "Configuring GitHub Actions runner..."
./config.sh --unattended --replace \
    --url "${GH_RUNNER_REPO_URL}" \
    --token "${GH_RUNNER_TOKEN}" \
    --name "${GH_RUNNER_NAME}" \
    --labels "${GH_RUNNER_LABELS}"

cleanup() {
    echo "Removing runner registration..."
    ./config.sh remove --token "${GH_RUNNER_TOKEN}"
    if [ -f /tmp/ui_pid ]; then
        kill $(cat /tmp/ui_pid) || true
    fi
    exit 0
}
trap 'cleanup' SIGINT SIGTERM

echo "Starting GitHub runner..."
exec ./runner.sh