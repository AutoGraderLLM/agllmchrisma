import sqlite3, os
from datetime import datetime

DB = os.path.join(os.getenv("HOME"), "agllmdatabase.db")

DDL = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS assignments;
DROP TABLE IF EXISTS submissions;
DROP TABLE IF EXISTS code_files;
DROP TABLE IF EXISTS feedback;
DROP TABLE IF EXISTS autograder_outputs;

CREATE TABLE students (
  student_repo TEXT PRIMARY KEY,
  additional_data TEXT
);

CREATE TABLE assignments (
  id INTEGER PRIMARY KEY,
  description TEXT NOT NULL
);

CREATE TABLE submissions (
  id            INTEGER PRIMARY KEY,
  student_repo  TEXT    NOT NULL REFERENCES students(student_repo),
  assignment_id INTEGER NOT NULL REFERENCES assignments(id),
  code TEXT,                     -- legacy single-blob (optional)
  submitted_at TEXT NOT NULL
);

CREATE TABLE code_files (
  id            INTEGER PRIMARY KEY,
  submission_id INTEGER NOT NULL REFERENCES submissions(id),
  filename      TEXT NOT NULL,
  code          TEXT NOT NULL
);

CREATE TABLE feedback (
  id            INTEGER PRIMARY KEY,
  submission_id INTEGER NOT NULL REFERENCES submissions(id),
  repo_name     TEXT    NOT NULL,
  feedback_text TEXT    NOT NULL,
  generated_at  TEXT    NOT NULL,
  reviewed      INTEGER NOT NULL DEFAULT 0,
  teacher_comments TEXT,
  reviewed_at   TEXT
);

CREATE TABLE autograder_outputs (
  id INTEGER PRIMARY KEY,
  submission_id INTEGER NOT NULL REFERENCES submissions(id),
  output TEXT NOT NULL,
  generated_at TEXT NOT NULL
);

CREATE INDEX idx_feedback_repo  ON feedback(repo_name, reviewed);
CREATE INDEX idx_codefiles_sub  ON code_files(submission_id);
"""

def build_demo():
    conn = sqlite3.connect(DB)
    conn.executescript(DDL)
    cur = conn.cursor()

    # demo rows -----------------------------------------------------
    cur.execute("INSERT INTO students VALUES('repo1','{\"name\":\"Sample\"}')")
    cur.execute("INSERT INTO assignments VALUES(1,'Demo')")
    now = datetime.utcnow().isoformat()+'Z'

    cur.execute("""INSERT INTO submissions
        (student_repo,assignment_id,submitted_at,code)
        VALUES('repo1',1,?, 'print(123)')""", (now,))
    sub_id = cur.lastrowid
    cur.executemany(
        "INSERT INTO code_files(submission_id,filename,code) VALUES (?,?,?)",
        [
          (sub_id,'main.py','print("Hello")'),
          (sub_id,'utils.py','def add(a,b): return a+b')
        ]
    )
    cur.execute("""INSERT INTO feedback
        (submission_id,repo_name,feedback_text,generated_at)
        VALUES(?,?,?,?)""",
        (sub_id,'repo1','Great start – think about edge cases.',now))

    conn.commit();  conn.close()
    print("DB ready →", DB)

if __name__ == "__main__":
    build_demo()
