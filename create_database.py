import sqlite3
import os
from datetime import datetime

def create_database():
    """Create SQLite database with the updated schema and pre-populate with sample data."""
    # Define the database path
    db_path = os.path.join(os.getenv("HOME"), "agllmdatabase.db")
    
    # Connect to SQLite database (it will create the file if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Define the schema
    schema = """
    PRAGMA foreign_keys = ON;

    -- Drop existing tables if they exist
    DROP TABLE IF EXISTS students;
    DROP TABLE IF EXISTS assignments;
    DROP TABLE IF EXISTS submissions;
    DROP TABLE IF EXISTS feedback;
    DROP TABLE IF EXISTS autograder_outputs;

    -- Table to store unique student repositories
    CREATE TABLE students (
        student_repo TEXT PRIMARY KEY,       -- Unique GitHub repository name (e.g., gamedev-cndlovu)
        additional_data TEXT                 -- Optional: For extra metadata
    );

    -- Table to store assignment descriptions
    CREATE TABLE assignments (
        id INTEGER PRIMARY KEY,              -- Unique identifier for each assignment
        description TEXT NOT NULL            -- Full description of the assignment
    );

    -- Table to store submissions
    CREATE TABLE submissions (
        id INTEGER PRIMARY KEY,              -- Unique identifier for each submission
        student_repo TEXT NOT NULL REFERENCES students(student_repo), -- Links to students
        assignment_id INTEGER NOT NULL REFERENCES assignments(id),    -- Links to assignments
        code TEXT NOT NULL,                  -- Entire code submitted as text
        submitted_at TEXT NOT NULL           -- UTC timestamp of the submission
    );

    -- Table to store feedback
    CREATE TABLE feedback (
        id INTEGER PRIMARY KEY,              -- Unique identifier for each feedback
        submission_id INTEGER NOT NULL REFERENCES submissions(id), -- Links to submissions
        feedback_text TEXT NOT NULL,         -- Feedback text from a file
        generated_at TEXT NOT NULL           -- UTC timestamp of feedback generation
    );

    -- Table to store autograder outputs
    CREATE TABLE autograder_outputs (
        id INTEGER PRIMARY KEY,              -- Unique identifier for each autograder output
        submission_id INTEGER NOT NULL REFERENCES submissions(id), -- Links to submissions
        output TEXT NOT NULL,                -- Results of the autograder
        generated_at TEXT NOT NULL           -- UTC timestamp of output generation
    );

    -- Indexes for performance
    CREATE INDEX idx_submissions_student_assignment ON submissions(student_repo, assignment_id);
    CREATE INDEX idx_feedback_submission_id ON feedback(submission_id);
    CREATE INDEX idx_autograder_outputs_submission_id ON autograder_outputs(submission_id);
    """
    try:
        # Execute the schema creation
        cursor.executescript(schema)
        print(f"Database created successfully at: {db_path}")
        
        # Pre-populate the database with sample data.
        # Insert a sample student.
        cursor.execute("""
            INSERT INTO students (student_repo, additional_data)
            VALUES (?, ?)
        """, ('repo1', 'Sample student repository'))
        
        # Insert a sample assignment.
        cursor.execute("""
            INSERT INTO assignments (id, description)
            VALUES (?, ?)
        """, (1, 'Sample Assignment: Build a simple app'))
        
        # Insert a sample submission.
        submitted_at = datetime.utcnow().isoformat() + "Z"
        cursor.execute("""
            INSERT INTO submissions (student_repo, assignment_id, code, submitted_at)
            VALUES (?, ?, ?, ?)
        """, ('repo1', 1, 'print("Hello, world!")', submitted_at))
        
        # Insert sample feedback for the submission.
        generated_at = datetime.utcnow().isoformat() + "Z"
        cursor.execute("""
            INSERT INTO feedback (submission_id, feedback_text, generated_at)
            VALUES (?, ?, ?)
        """, (1, 'Good attempt, but consider adding error handling.', generated_at))
        
        # Insert sample autograder output.
        generated_at2 = datetime.utcnow().isoformat() + "Z"
        cursor.execute("""
            INSERT INTO autograder_outputs (submission_id, output, generated_at)
            VALUES (?, ?, ?)
        """, (1, 'All tests passed', generated_at2))
        
        # Commit changes
        conn.commit()
        print("Sample data inserted successfully.")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        # Close the connection
        conn.close()

# Run the function to create the database and pre-populate data
if __name__ == "__main__":
    create_database()