from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
import sqlite3, csv, io
from datetime import datetime
import hashlib

app = FastAPI()
DB_PATH = "/tmp/homework.db"

# ================= DATABASE =================
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS homework (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        homework TEXT,
        student TEXT,
        priority INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ================= DATA =================
def load_records(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id,date,homework,student,priority
    FROM homework
    WHERE user_id=?
    ORDER BY priority DESC,id DESC
    """,(user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{
        "ID":r[0],"Date":r[1],
        "Homework":r[2],
        "Student":r[3],"Priority":r[4]
    } for r in rows]

def get_counts(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT student,COUNT(*)
    FROM homework
    WHERE user_id=?
    GROUP BY student
    """,(user_id,))
    data = dict(cursor.fetchall())
    conn.close()
    return data

# ================= AUTH =================
@app.get("/login", response_class=HTMLResponse)
def login_page():
    return """
    <form method="post">
    <input name="username" required>
    <input name="password" type="password" required>
    <button>Login</button>
    </form>
    """

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username=? AND password=?",
                   (username, hash_pw(password)))
    user = cursor.fetchone()
    conn.close()
    if user:
        res = RedirectResponse("/",303)
        res.set_cookie("user_id", str(user[0]))
        return res
    return RedirectResponse("/login",303)

@app.get("/logout")
def logout():
    res = RedirectResponse("/login",303)
    res.delete_cookie("user_id")
    return res

# ================= MAIN =================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/login")

    records = load_records(user_id)
    counts = get_counts(user_id)

    total = len(records)
    unique = len(counts)
    priority_count = len([r for r in records if r["Priority"]])

    priority_students = [r["Student"] for r in records if r["Priority"]]
    priority_display = ", ".join(set(priority_students)) if priority_students else "None 🎉"

    rows = "".join(f"""
    <tr>
    <td>{r['Date']}</td>
    <td>{r['Homework']}</td>
    <td>{r['Student']}</td>
    <td>
    <form action="/delete/{r['ID']}" method="post">
    <button class="delete">✕</button>
    </form>
    </td>
    </tr>
    """ for r in records)

    return f"""
<html>
<head>
<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600&display=swap" rel="stylesheet">
<style>
*{{font-family:'Fredoka';box-sizing:border-box;}}

body{{
background:linear-gradient(135deg,#eef2ff,#fdf4ff);
padding:30px;
}}

.container{{max-width:1100px;margin:auto;}}

.header{{
display:flex;
justify-content:space-between;
align-items:center;
margin-bottom:25px;
}}

.card{{
background:white;
padding:22px;
border-radius:18px;
margin-bottom:25px;
box-shadow:0 8px 20px rgba(0,0,0,.08);
}}

.grid{{
display:grid;
grid-template-columns:repeat(3,1fr);
gap:20px;
margin-bottom:25px;
}}

.big{{font-size:28px;color:#6366f1;}}

button{{
border:none;
padding:10px 14px;
border-radius:12px;
background:#6366f1;
color:white;
cursor:pointer;
}}

.delete{{background:#ef4444;}}

input{{
width:100%;
padding:10px;
margin:8px 0;
border-radius:12px;
border:2px solid #ddd;
}}

.priority-row{{
display:flex;
align-items:center;
gap:8px;
margin-top:8px;
}}

.records-header{{
display:flex;
justify-content:space-between;
align-items:center;
background:linear-gradient(90deg,#6366f1,#a78bfa);
color:white;
padding:14px 18px;
border-radius:14px;
margin-bottom:12px;
}}

table{{
width:100%;
border-collapse:collapse;
}}

th,td{{
padding:12px;
text-align:left;
}}

th{{
background:#f3f4f6;
}}

tr:hover{{background:#f9fafb;}}

</style>
</head>
<body>

<div class="container">

<div class="header">
<h1>📚 Homework Tracker</h1>
<a href="/logout"><button>Logout</button></a>
</div>

<div class="grid">
<div class="card">Total<div class="big">{total}</div></div>
<div class="card">Students<div class="big">{unique}</div></div>
<div class="card">Priority<div class="big">{priority_count}</div></div>
</div>

<div class="card">
<h3>Add Record</h3>
<form method="post" action="/add">
<input name="homework" placeholder="Homework">
<input name="student" placeholder="Student">

<div class="priority-row">
<input type="checkbox" name="priority">
<label>Priority</label>
</div>

<br>
<button>Add ✨</button>
</form>
</div>

<div class="card">
<h3>Priority Student</h3>
<b>{priority_display}</b>
</div>

<div class="card">

<div class="records-header">
<h3>Records</h3>
<a href="/export"><button style="background:white;color:#6366f1;">Export</button></a>
</div>

<table>
<tr>
<th>Date</th>
<th>Homework</th>
<th>Student</th>
<th>Action</th>
</tr>
{rows}
</table>

</div>

</div>
</body>
</html>
"""

# ================= ADD =================
@app.post("/add")
def add(request: Request,
homework: str = Form(...),
student: str = Form(...),
priority: str = Form(None)):

    if not homework or not student:
        return RedirectResponse("/",303)

    user_id = request.cookies.get("user_id")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO homework VALUES (NULL,?,?,?,?,?)
    """,(user_id,
        datetime.now().strftime("%Y-%m-%d"),
        homework,student,
        1 if priority else 0))
    conn.commit()
    conn.close()

    return RedirectResponse("/",303)

# ================= DELETE =================
@app.post("/delete/{id}")
def delete(request: Request, id: int):
    user_id = request.cookies.get("user_id")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM homework WHERE id=? AND user_id=?", (id,user_id))
    conn.commit()
    conn.close()
    return RedirectResponse("/",303)

# ================= EXPORT =================
@app.get("/export")
def export(request: Request):
    user_id = request.cookies.get("user_id")
    records = load_records(user_id)

    output = io.StringIO()
    writer = csv.writer(output)

    # FIXED DATE FORMAT (Excel friendly)
    writer.writerow(["Date","Homework","Student","Priority"])

    for r in records:
        writer.writerow([
            r["Date"],   # already YYYY-MM-DD → Excel safe
            r["Homework"],
            r["Student"],
            "Yes" if r["Priority"] else "No"
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=homework.csv"}
    )
