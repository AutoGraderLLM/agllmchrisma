from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3, os, markdown
from datetime import datetime

DB = os.getenv("AGLLM_DB", os.path.join(os.getenv("HOME"), "agllmdatabase.db"))

def q(sql, args=()):
    with sqlite3.connect(DB) as c:
        c.row_factory = sqlite3.Row
        return c.execute(sql, args).fetchall()

def md(txt):  # GitHub-style markdown→HTML
    return markdown.markdown(txt, extensions=["fenced_code", "codehilite", "tables"])

def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "replace-me-in-prod"

    # ── home – list repos with pending items
    @app.route("/")
    def choose_student():
        repos = q("""
            SELECT repo_name, COUNT(*) AS cnt
              FROM feedback
             WHERE reviewed = 0
          GROUP BY repo_name
          ORDER BY repo_name
        """)
        return render_template("students.html", students=repos)

    # ── repo detail – show all un-reviewed feedback
    @app.route("/repo/<repo>")
    def student_detail(repo):
        rows = q("""
            SELECT f.*, cf.filename, cf.code
              FROM feedback     f
              JOIN submissions  s  ON s.id = f.submission_id
              LEFT JOIN code_files cf ON cf.submission_id = s.id
             WHERE f.reviewed = 0
               AND f.repo_name = ?
          ORDER BY f.generated_at DESC, cf.filename
        """, (repo,))

        fb_items = []
        for r in rows:
            fb = next((x for x in fb_items if x["id"] == r["id"]), None)
            if not fb:
                fb = dict(r)
                fb["feedback_html"] = md(r["feedback_text"])
                fb["code_files"] = []
                fb_items.append(fb)
            if r["filename"]:  # may be NULL if you haven’t written code_files yet
                fb["code_files"].append({"filename": r["filename"], "code": r["code"]})
            elif not fb["code_files"] and r["code"]:
                # fallback to legacy single-blob
                fb["code_files"].append({"filename": "submitted_code.py", "code": r["code"]})

        return render_template("review_feedback.html", repo=repo, feedbacks=fb_items)

    # ── mark reviewed
    @app.post("/review/<int:fid>")
    def mark_reviewed(fid):
        comments = request.form.get("teacher_comments", "")
        q("""UPDATE feedback
                SET reviewed = 1,
                    reviewed_at = ?,
                    teacher_comments = ?
              WHERE id = ?""",
          (datetime.utcnow().isoformat(), comments, fid))
        flash("Saved ✔")
        return redirect(url_for("choose_student"))

    # legacy redirect
    @app.route("/feedback/unreviewed")
    def legacy_redirect():
        return redirect(url_for("choose_student"), code=301)

    return app

if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5003, debug=True)
