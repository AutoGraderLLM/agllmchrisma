#!/usr/bin/env python3
"""
control_code.py
───────────────
• Collects student repo name from CLI
• Reads all *.py files, autograder output, README
• Sends a prompt to the Ollama “ux1” model
• Writes markdown feedback to ~/logs/feedback.md
• Inserts rows into the **new schema**:

    submissions      (legacy `code` column kept)
    code_files       (one row per file)
    autograder_outputs
    feedback         (repo_name + reviewed flag)

Assumes agllmdatabase.db is at $HOME/agllmdatabase.db (override with $AGLLM_DB).
"""

import os, sys, sqlite3, subprocess, shutil
from pathlib import Path
from datetime import datetime

# ─────────────────────────── config ─────────────────────────────
DB_PATH = os.getenv("AGLLM_DB",
                    os.path.join(os.getenv("HOME"), "agllmdatabase.db"))
LOGS_DIR = Path(os.getenv("HOME") or ".").joinpath("logs")
STUDENT_CODE_DIR = LOGS_DIR / "studentcode"
AUTO_FILE = LOGS_DIR / "autograder_output.txt"
README_FILE = LOGS_DIR / "README.md"
FEEDBACK_MD = LOGS_DIR / "feedback.md"
ASSIGNMENT_ID = 101
TEST_ID       = 1001                     # kept for future use
OLLAMA_MODEL  = "ux1"

# ─────────────────────────── helpers ────────────────────────────
def err(msg: str):
    print(f"❌ {msg}", file=sys.stderr); sys.exit(1)

def read_file(path: Path) -> str:
    for enc in ("utf-8", "ISO-8859-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    print(f"Warning: could not decode {path.name}")
    return ""

def run_ollama(prompt: str) -> str:
    res = subprocess.run(
        ["ollama", "run", OLLAMA_MODEL],
        input=prompt,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if res.returncode != 0:
        err(f"Ollama error ⇒ {res.stderr.strip()}")
    return res.stdout

# ─────────────────────────── main flow ──────────────────────────
def main() -> None:
    # 0️⃣ student repo
    if len(sys.argv) < 2:
        err("Usage: control_code.py <repo_name>")
    repo_name = sys.argv[1]

    # 1️⃣ gather code files
    if not STUDENT_CODE_DIR.is_dir():
        err(f"{STUDENT_CODE_DIR} not found")
    # NEW (language-agnostic)
    code_files = sorted(
        p for p in STUDENT_CODE_DIR.rglob("*")
        if p.is_file() and not p.name.startswith(".")     # skip dot-files
    )
    if not code_files:
        err(f"No files found in {STUDENT_CODE_DIR}")

    student_code_blob = ""
    for p in code_files:
        student_code_blob += f"File: {p.relative_to(STUDENT_CODE_DIR)}\n"
        student_code_blob += read_file(p) + "\n\n"

    autograder_out = read_file(AUTO_FILE)    if AUTO_FILE.exists() else ""
    professor_inst = read_file(README_FILE)  if README_FILE.exists() else ""

    # 2️⃣ query model
    prompt = (
        "DO NOT CORRECT THE CODE! Provide question-based guided feedback only.\n\n"
        f"**Student Code**\n{student_code_blob}\n"
        f"**Autograder Output**\n{autograder_out}\n"
        f"**Professor Instructions**\n{professor_inst}\n"
    )
    feedback_text = run_ollama(prompt)

    # 3️⃣ save markdown
    FEEDBACK_MD.write_text(
        f"# Feedback for {repo_name}\n\n{feedback_text}",
        encoding="utf-8"
    )
    print(f"📄  Feedback saved → {FEEDBACK_MD}")

    # 4️⃣ insert into SQLite
    ts = datetime.utcnow().isoformat() + "Z"
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    try:
        # submissions row (legacy `code` keeps full blob for quick view)
        cur.execute(
            """INSERT INTO submissions
                 (student_repo, assignment_id, code, submitted_at)
               VALUES (?,?,?,?)""",
            (repo_name, ASSIGNMENT_ID, student_code_blob, ts)
        )
        submission_id = cur.lastrowid

        # code_files rows
        for p in code_files:
            cur.execute(
                "INSERT INTO code_files(submission_id, filename, code) VALUES (?,?,?)",
                (submission_id, str(p.relative_to(STUDENT_CODE_DIR)), read_file(p))
            )

        # autograder output
        cur.execute(
            "INSERT INTO autograder_outputs(submission_id, output, generated_at) VALUES (?,?,?)",
            (submission_id, autograder_out, ts)
        )

        # feedback row (reviewed = 0)
        cur.execute(
            """INSERT INTO feedback
                   (submission_id, repo_name, feedback_text, generated_at)
               VALUES (?,?,?,?)""",
            (submission_id, repo_name, feedback_text, ts)
        )

        conn.commit()
        print("✅ Data inserted into agllmdatabase.db")
    except sqlite3.Error as e:
        conn.rollback()
        err(f"SQLite error → {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
