import os
import sqlite3
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = "insecure-secret-key"

FLAG = os.environ.get("CTF_FLAG", "CTF{placeholder}")
DB_PATH = "/tmp/idor.db"

STYLE = """
<style>
body{font-family:monospace;background:#1a1a2e;color:#eee;margin:0;padding:20px}
nav{background:#16213e;padding:12px 20px;margin:-20px -20px 20px;display:flex;gap:20px;align-items:center}
nav a{color:#aaa;text-decoration:none}nav a:hover{color:#fff}
.box{background:#16213e;padding:16px;border-radius:8px;margin-bottom:16px}
.field{display:flex;gap:12px;padding:8px 0;border-bottom:1px solid #2a2a4e}
.field:last-child{border-bottom:none}
.label{color:#aaa;width:140px;flex-shrink:0}
.value{color:#fff}
.flag-value{color:#0f0;font-family:monospace}
button{padding:8px 16px;background:#e94560;border:none;color:white;border-radius:4px;cursor:pointer}
input{padding:8px;background:#0f3460;border:1px solid #444;color:#eee;border-radius:4px}
.nav-user{margin-left:auto;color:#aaa;font-size:13px}
</style>
"""


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        grade TEXT,
        notes TEXT
    )""")
    conn.execute("DELETE FROM students")
    # Admin record with the flag
    conn.execute("INSERT INTO students VALUES (1, 'Admin', 'admin@school.es', 'N/A', ?)", (FLAG,))
    conn.execute("INSERT INTO students VALUES (2, 'María García', 'maria@school.es', '8.5', 'Good progress')")
    conn.execute("INSERT INTO students VALUES (3, 'Carlos López', 'carlos@school.es', '7.2', 'Needs improvement')")
    conn.execute("INSERT INTO students VALUES (4, 'Ana Martínez', 'ana@school.es', '9.1', 'Excellent student')")
    # The student is logged in as ID 5
    conn.execute("INSERT INTO students VALUES (5, 'You', 'student@school.es', '6.8', 'Keep it up!')")
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return f"""<!DOCTYPE html><html><head><title>Student Portal</title>{STYLE}</head><body>
    <nav><strong style="color:#e94560">Student Portal</strong>
    <a href="/record/5">My Record</a>
    <span class="nav-user">Logged in as: student (ID: 5)</span>
    </nav>
    <div class="box">
        <h2>Welcome to the Student Portal</h2>
        <p>View your academic record using the link above.</p>
    </div>
    </body></html>"""


@app.route("/record/<int:student_id>")
def record(student_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT id, name, email, grade, notes FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()
    conn.close()

    if not row:
        return f"""<!DOCTYPE html><html><head><title>Not Found</title>{STYLE}</head><body>
        <nav><strong style="color:#e94560">Student Portal</strong>
        <a href="/record/5">My Record</a></nav>
        <div class="box"><p style="color:#e94560">Record not found.</p></div>
        </body></html>""", 404

    sid, name, email, grade, notes = row

    # Flag is in the notes field of record ID 1
    notes_display = f'<span class="flag-value">{notes}</span>' if sid == 1 else notes

    # INTENTIONALLY VULNERABLE — no authorization check
    # Should verify: if student_id != current_user.id: return 403
    return f"""<!DOCTYPE html><html><head><title>Record #{sid}</title>{STYLE}</head><body>
    <nav><strong style="color:#e94560">Student Portal</strong>
    <a href="/record/5">My Record</a>
    <span class="nav-user">Logged in as: student (ID: 5)</span>
    </nav>
    <div class="box">
        <h2>Academic Record</h2>
        <div class="field"><span class="label">ID</span><span class="value">{sid}</span></div>
        <div class="field"><span class="label">Name</span><span class="value">{name}</span></div>
        <div class="field"><span class="label">Email</span><span class="value">{email}</span></div>
        <div class="field"><span class="label">Grade</span><span class="value">{grade}</span></div>
        <div class="field"><span class="label">Notes</span><span class="value">{notes_display}</span></div>
    </div>
    </body></html>"""


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
