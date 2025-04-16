import sqlite3
import os
from datetime import datetime

def create_database():
    """Create SQLite database with the updated schema and pre‑populate with sample data."""
    # Path for the SQLite file
    db_path = os.path.join(os.getenv("HOME"), "agllmdatabase.db")
    
    # Connect (creates file if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # === SCHEMA DEFINITION ===
    schema = """
    PRAGMA foreign_keys = ON;

    -- Drop any existing tables
    DROP TABLE IF EXISTS students;
    DROP TABLE IF EXISTS assignments;
    DROP TABLE IF EXISTS submissions;
    DROP TABLE IF EXISTS feedback;
    DROP TABLE IF EXISTS autograder_outputs;

    -- Students table
    CREATE TABLE students (
        student_repo TEXT PRIMARY KEY,
        additional_data TEXT
    );

    -- Assignments table
    CREATE TABLE assignments (
        id          INTEGER PRIMARY KEY,
        description TEXT    NOT NULL
    );

    -- Submissions table
    CREATE TABLE submissions (
        id             INTEGER PRIMARY KEY,
        student_repo   TEXT    NOT NULL REFERENCES students(student_repo),
        assignment_id  INTEGER NOT NULL REFERENCES assignments(id),
        code           TEXT    NOT NULL,
        submitted_at   TEXT    NOT NULL
    );

    -- Feedback table (now with status & teacher_edited_response)
    CREATE TABLE feedback (
        id                       INTEGER PRIMARY KEY,
        submission_id            INTEGER NOT NULL REFERENCES submissions(id),
        feedback_text            TEXT    NOT NULL,
        generated_at             TEXT    NOT NULL,
        status                   TEXT    NOT NULL DEFAULT 'UNREVIEWED',
        teacher_edited_response  TEXT
    );

    -- Autograder outputs
    CREATE TABLE autograder_outputs (
        id            INTEGER PRIMARY KEY,
        submission_id INTEGER NOT NULL REFERENCES submissions(id),
        output        TEXT    NOT NULL,
        generated_at  TEXT    NOT NULL
    );

    -- Indexes for faster lookups
    CREATE INDEX idx_submissions_student_assignment
        ON submissions(student_repo, assignment_id);
    CREATE INDEX idx_feedback_submission_id
        ON feedback(submission_id);
    CREATE INDEX idx_autograder_outputs_submission_id
        ON autograder_outputs(submission_id);
    """

    try:
        # Create all tables & indexes
        cursor.executescript(schema)
        print(f"Database created successfully at: {db_path}")

        # === PRE‑POPULATE WITH SAMPLE DATA ===

        # 1) A sample student repo
        cursor.execute(
            "INSERT INTO students(student_repo, additional_data) VALUES (?, ?)",
            ('repo1', '{"name": "Sample Student"}')
        )

        # 2) A sample assignment
        cursor.execute(
            "INSERT INTO assignments(id, description) VALUES (?, ?)",
            (1, "Sample Assignment")
        )

        # 3) A sample submission
        submitted_at = datetime.utcnow().isoformat() + "Z"
        cursor.execute(
            "INSERT INTO submissions(student_repo, assignment_id, code, submitted_at) VALUES (?, ?, ?, ?)",
            ('repo1', 1, 'print("Hello, world!")', submitted_at)
        )

        # 4) A sample unreviewed feedback row
        generated_at = datetime.utcnow().isoformat() + "Z"
        cursor.execute(
            "INSERT INTO feedback(submission_id, feedback_text, generated_at) VALUES (?, ?, ?)",
            (1, "Good attempt, but consider adding error handling.", generated_at)
        )

        # 5) A sample autograder output
        generated_at2 = datetime.utcnow().isoformat() + "Z"
        cursor.execute(
            "INSERT INTO autograder_outputs(submission_id, output, generated_at) VALUES (?, ?, ?)",
            (1, "All tests passed", generated_at2)
        )

        # Commit everything
        conn.commit()
        print("Sample data inserted successfully.")

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")

    finally:
        conn.close()

if __name__ == "__main__":
    create_database()
