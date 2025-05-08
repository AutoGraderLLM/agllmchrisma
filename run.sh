#!/bin/bash
set -e

#─────────────────────────
# One‑Time Setup
#─────────────────────────
if [ ! -f /tmp/setup_done ]; then
  echo "Installing Rich …"
  pip install --user rich

  cd /app || { echo "/app missing"; exit 1; }

  echo "Running create_database.py…"
  python3 create_database.py
  python3 verify_db.py

  # Copy control_code.py to $HOME only if it does NOT exist yet
  if [ ! -f "$HOME/control_code.py" ]; then
      echo "Copying default control_code.py to \$HOME"
      cp /app/control_code.py "$HOME/"
  else
      echo "\$HOME/control_code.py already present — leaving repo‑version intact"
  fi

  echo "Starting teacher UI on :5003 …"
  python3 teacher_ui.py &
  echo $! > /tmp/ui_pid

  touch /tmp/setup_done
fi

#─────────────────────────
# GitHub Runner Section
#─────────────────────────
cd /actions-runner

echo "Removing previous runner config (if any)…"
./config.sh remove --token "${GH_RUNNER_TOKEN}" || true

echo "Configuring runner …"
./config.sh --unattended --replace \
  --url    "${GH_RUNNER_REPO_URL}" \
  --token  "${GH_RUNNER_TOKEN}"    \
  --name   "${GH_RUNNER_NAME}"     \
  --labels "${GH_RUNNER_LABELS}"

cleanup() {
  echo "Deregistering runner …"
  ./config.sh remove --token "${GH_RUNNER_TOKEN}" || true
  [ -f /tmp/ui_pid ] && kill "$(cat /tmp/ui_pid)" || true
  exit 0
}
trap cleanup SIGINT SIGTERM

echo "Runner up — listening for jobs."
exec ./runner.sh
