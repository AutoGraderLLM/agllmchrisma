#!/usr/bin/env python3
import os, sqlite3, markdown
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

DB = os.getenv("AGLLM_DB",
               os.path.join(os.getenv("HOME"), "agllmdatabase.db"))

def q(sql, args=()):
    with sqlite3.connect(DB) as c:
        c.row_factory = sqlite3.Row
        return c.execute(sql, args).fetchall()

def md(txt):
    return markdown.markdown(txt, extensions=["fenced_code", "codehilite", "tables"])

def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "replace-me-in-prod"

    # 1️⃣  home – repo list with red/green badge
    @app.route("/")
    def choose_student():
        repos = q("""
            WITH repeated AS (
              SELECT repo_name,
                     submission_id,
                     SUM(hit) AS hits
                FROM (
                     SELECT f.repo_name,
                            f.submission_id,
                            /* hit = 1 if the comment contains the keyword */
                            CASE
                              WHEN instr(lower(f.teacher_comments), lower(value)) > 0
                              THEN 1 ELSE 0
                            END AS hit
                       FROM feedback  f
                  CROSS JOIN
                       json_each(json_array('memory','leak','edge','case'))
                     )
            GROUP BY repo_name, submission_id
            HAVING hits >= 3             -- same keyword group ≥3 times
            )
            SELECT r.repo_name,
                   COUNT(*)                   AS cnt,
                   EXISTS ( SELECT 1
                              FROM repeated bad
                             WHERE bad.repo_name = r.repo_name
                         )                   AS red_flag
              FROM feedback r
             WHERE r.reviewed = 0
          GROUP BY r.repo_name
          ORDER BY r.repo_name;
        """)
        return render_template("students.html", students=repos)

    # ---------- the rest of the file is unchanged -----------------
    @app.route("/repo/<repo>")
    def student_detail(repo):
        rows = q("""
            SELECT f.*, cf.filename, cf.code, s.code AS legacy_code
              FROM feedback   f
              JOIN submissions s  ON s.id = f.submission_id
         LEFT JOIN code_files cf ON cf.submission_id = s.id
             WHERE f.reviewed = 0 AND f.repo_name = ?
          ORDER BY f.generated_at DESC, cf.filename
        """, (repo,))

        items = []
        for r in rows:
            fb = next((x for x in items if x["id"] == r["id"]), None)
            if not fb:
                fb = dict(r)
                fb["feedback_html"] = md(r["feedback_text"])
                fb["code_files"] = []
                items.append(fb)
            if r["filename"]:
                fb["code_files"].append({"filename": r["filename"], "code": r["code"]})

        for fb in items:
            if not fb["code_files"] and fb["legacy_code"]:
                fb["code_files"].append({"filename": "submission.py", "code": fb["legacy_code"]})

        return render_template("review_feedback.html", repo=repo, feedbacks=items)

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

    @app.route("/feedback/unreviewed")
    def legacy_redirect():
        return redirect(url_for("choose_student"), code=301)

    return app

if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5003, debug=True)