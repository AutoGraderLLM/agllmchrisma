"""
teacher_ui.py
─────────────
Flask dashboard for AG-LLM grading.

Key features
• Reads the SAME database file your pipeline already populates
  (defaults to $HOME/agllmdatabase.db, overridable with $AGLLM_DB).
• Home page lists every repo that still has un-reviewed feedback.
• Click a repo → see all pending feedback items, markdown-rendered,
  with **all** submitted code files.
• Teacher can add comments & mark each item reviewed.
"""

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
import markdown
import sqlite3
import os
from datetime import datetime

# ────────────────────────────────────────────────────────────────
#  Database location (override with env-var if you ever need to)
# ────────────────────────────────────────────────────────────────
DB = os.getenv(
    "AGLLM_DB",
    os.path.join(os.getenv("HOME"), "agllmdatabase.db"),
)


# ────────────────────────────────────────────────────────────────
#  Tiny helper wrappers
# ────────────────────────────────────────────────────────────────
def run_sql(query: str, args: tuple = (), many: bool = False):
    """
    Simple wrapper around sqlite3; returns list[Row].
    If `many` is True we assume `args` is an iterable of arg-tuples.
    """
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        cur = (
            conn.executemany(query, args) if many else conn.execute(query, args)
        )
        return cur.fetchall()


def md(html_text: str) -> str:
    """GitHub-flavoured markdown → HTML (with code fences)."""
    return markdown.markdown(
        html_text,
        extensions=["fenced_code", "codehilite", "tables"],
    )


# ────────────────────────────────────────────────────────────────
#  Flask factory
# ────────────────────────────────────────────────────────────────
def build_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "replace-me-in-production"

    # ————————————————————————————————————————————————
    #  1️⃣  HOME  – choose a student repo
    # ————————————————————————————————————————————————
    @app.route("/")
    def choose_student():
        rows = run_sql(
            """
            SELECT repo_name, COUNT(*) AS cnt
              FROM feedback
             WHERE reviewed = 0
          GROUP BY repo_name
          ORDER BY repo_name;
            """
        )
        return render_template("students.html", students=rows)

    # ————————————————————————————————————————————————
    #  2️⃣  STUDENT DETAIL  – all un-reviewed for one repo
    # ————————————————————————————————————————————————
    @app.route("/repo/<repo>")
    def student_detail(repo: str):
        rows = run_sql(
            """
            SELECT f.*, cf.filename, cf.code
              FROM feedback f
              JOIN code_files cf ON cf.feedback_id = f.id
             WHERE f.reviewed = 0
               AND f.repo_name = ?
          ORDER BY f.generated_at DESC, cf.filename;
            """,
            (repo,),
        )

        # build list[dict] where each dict == one feedback item
        feedbacks: list[dict] = []
        for r in rows:
            fb = next((x for x in feedbacks if x["id"] == r["id"]), None)
            if not fb:
                fb = dict(r)
                fb["feedback_html"] = md(r["feedback_text"])
                fb["code_files"] = []
                feedbacks.append(fb)
            fb["code_files"].append(
                {"filename": r["filename"], "code": r["code"]}
            )

        return render_template(
            "review_feedback.html", repo=repo, feedbacks=feedbacks
        )

    # ————————————————————————————————————————————————
    #  3️⃣  POST  – teacher marks feedback reviewed
    # ————————————————————————————————————————————————
    @app.post("/review/<int:fid>")
    def mark_reviewed(fid: int):
        comments = request.form.get("teacher_comments", "")
        run_sql(
            """
            UPDATE feedback
               SET teacher_comments = ?,
                   reviewed        = 1,
                   reviewed_at     = ?
             WHERE id = ?;
            """,
            (comments, datetime.utcnow().isoformat(), fid),
        )
        flash("Saved ✔")
        return redirect(url_for("choose_student"))

    # ————————————————————————————————————————————————
    #  4️⃣  Legacy redirect (old bookmark)
    # ————————————————————————————————————————————————
    @app.route("/feedback/unreviewed")
    def legacy_redirect():
        return redirect(url_for("choose_student"), code=301)

    return app


# ────────────────────────────────────────────────────────────────
#  CLI entry-point  (works fine in Flask debug OR production WSGI)
# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    build_app().run(host="0.0.0.0", port=5003, debug=True)
