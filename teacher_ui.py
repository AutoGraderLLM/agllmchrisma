#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

# Path to your SQLite database. Adjust as needed.
DB_PATH = os.path.join(os.getenv("HOME", "."), "agllmdatabase.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enables column access by name: row['column_name']
    return conn

@app.route('/feedback/unreviewed')
def list_unreviewed_feedback():
    """
    Query the database for all unreviewed feedback entries, joining with the submissions
    to show the corresponding student code.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT f.id, f.submission_id, f.feedback_text, f.generated_at, s.code
        FROM feedback f
        JOIN submissions s ON f.submission_id = s.id
        WHERE f.status = 'UNREVIEWED'
        ORDER BY f.generated_at DESC;
    """
    cursor.execute(query)
    feedbacks = cursor.fetchall()
    conn.close()
    return render_template('review_feedback.html', feedbacks=feedbacks)

@app.route('/feedback/review/<int:feedback_id>', methods=['POST'])
def review_feedback(feedback_id):
    """
    Accept teacher corrections/comments and update the feedback record as REVIEWED.
    """
    teacher_comments = request.form.get('teacher_comments', '')
    conn = get_db_connection()
    cursor = conn.cursor()
    update_query = """
        UPDATE feedback
        SET teacher_edited_response = ?,
            status = 'REVIEWED'
        WHERE id = ?;
    """
    cursor.execute(update_query, (teacher_comments, feedback_id))
    conn.commit()
    conn.close()
    return redirect(url_for('list_unreviewed_feedback'))

if __name__ == '__main__':
    # Read the port from the environment variable TEACHER_UI_PORT (default to 5001)
    port = int(os.environ.get("TEACHER_UI_PORT", 5000))
    app.run(host='0.0.0.0', port=port)