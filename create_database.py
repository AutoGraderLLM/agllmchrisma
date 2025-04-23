# create_database.py  (complete replacement)
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
  id          INTEGER PRIMARY KEY,
  description TEXT NOT NULL
);

CREATE TABLE submissions (
  id             INTEGER PRIMARY KEY,
  student_repo   TEXT    NOT NULL REFERENCES students(student_repo),
  assignment_id  INTEGER NOT NULL REFERENCES assignments(id),
  submitted_at   TEXT    NOT NULL
);

-- NEW: each file attached to a submission
CREATE TABLE code_files (
  id            INTEGER PRIMARY KEY,
  submission_id INTEGER NOT NULL REFERENCES submissions(id),
  filename      TEXT    NOT NULL,
  code          TEXT    NOT NULL
);

CREATE TABLE feedback (
  id                  INTEGER PRIMARY KEY,
  submission_id       INTEGER NOT NULL REFERENCES submissions(id),
  repo_name           TEXT    NOT NULL,                -- redundant but handy
  feedback_text       TEXT    NOT NULL,
  generated_at        TEXT    NOT NULL,
  reviewed            INTEGER NOT NULL DEFAULT 0,      -- 0 = todo, 1 = done
  teacher_comments    TEXT,
  reviewed_at         TEXT
);

CREATE TABLE autograder_outputs (
  id            INTEGER PRIMARY KEY,
  submission_id INTEGER NOT NULL REFERENCES submissions(id),
  output        TEXT    NOT NULL,
  generated_at  TEXT    NOT NULL
);

CREATE INDEX idx_feedback_repo   ON feedback(repo_name, reviewed);
CREATE INDEX idx_codefiles_sub   ON code_files(submission_id);
"""

def build_demo():
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    cur.executescript(DDL)

    # demo student / assignment
    cur.execute("INSERT INTO students VALUES (?,?)",
                ('repo1', '{"name":"Sample Student"}'))
    cur.execute("INSERT INTO assignments(id,description) VALUES(1,'Demo')")
    conn.commit()

    # demo submission + two files
    now = datetime.utcnow().isoformat()+'Z'
    cur.execute("INSERT INTO submissions(student_repo,assignment_id,submitted_at) "
                "VALUES('repo1',1,?)", (now,))
    sub_id = cur.lastrowid
    cur.executemany(
        "INSERT INTO code_files(submission_id,filename,code) VALUES(?,?,?)",
        [
          (sub_id,'main.py','print("Hello")'),
          (sub_id,'utils.py','def add(a,b): return a+b'),
        ]
    )

    # demo unreviewed feedback
    cur.execute("""INSERT INTO feedback
        (submission_id,repo_name,feedback_text,generated_at)
        VALUES(?,?,?,?)""",
        (sub_id,'repo1','Great start, but think about edge cases.',now))
    conn.commit()
    conn.close()
    print("DB rebuilt with sample data ✔")

if __name__ == "__main__":
    build_demo()
