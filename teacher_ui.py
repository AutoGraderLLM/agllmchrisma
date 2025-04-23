"""
Teacher review dashboard  – student selector + markdown + multi-file view
"""
from flask import Flask, render_template, request, redirect, url_for, flash
import markdown, sqlite3
from pathlib import Path
from datetime import datetime

DB = Path(__file__).with_name("teacher.db")

def run_sql(query, args=(), many=False):
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.executemany(query, args) if many else conn.execute(query, args)
        return cur.fetchall()

def md(html):
    return markdown.markdown(html, extensions=["fenced_code", "codehilite", "tables"])

def build_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "super-secret"                      # replace in prod

    # ── 1. HOME – list students with pending reviews ──────────────────
    @app.route("/")
    def choose_student():
        rows = run_sql(
            "SELECT DISTINCT repo_name, COUNT(*) AS cnt "
            "FROM feedback WHERE reviewed = 0 GROUP BY repo_name "
            "ORDER BY repo_name"
        )
        return render_template("students.html", students=rows)

    # ── 2. STUDENT DETAIL – all unreviewed feedback for one repo ──────
    @app.route("/repo/<repo>")
    def student_detail(repo: str):
        rows = run_sql(
            """
            SELECT f.*, cf.filename, cf.code
              FROM feedback f
              JOIN code_files cf ON cf.feedback_id = f.id
             WHERE f.reviewed = 0 AND f.repo_name = ?
             ORDER BY f.generated_at DESC, cf.filename
            """,
            (repo,),
        )
        feedbacks = []
        for r in rows:
            fb = next((x for x in feedbacks if x["id"] == r["id"]), None)
            if not fb:
                fb = dict(r)
                fb["feedback_html"] = md(r["feedback_text"])
                fb["code_files"] = []
                feedbacks.append(fb)
            fb["code_files"].append({"filename": r["filename"], "code": r["code"]})
        return render_template("review_feedback.html", repo=repo, feedbacks=feedbacks)

    # ── 3. POST – mark a feedback as reviewed ─────────────────────────
    @app.post("/review/<int:fid>")
    def mark_reviewed(fid: int):
        comments = request.form.get("teacher_comments", "")
        run_sql(
            "UPDATE feedback SET teacher_comments=?, reviewed=1, reviewed_at=? WHERE id=?",
            (comments, datetime.utcnow().isoformat(), fid),
        )
        flash("Saved ✔")
        # redirect back to the current student's page
        repo = request.form.get("repo")
        return redirect(url_for("student_detail", repo=repo))

    return app

if __name__ == "__main__":
    build_app().run(host="0.0.0.0", port=5003, debug=True)
