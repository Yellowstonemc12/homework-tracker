from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
import sqlite3
from datetime import datetime
import hashlib
import io
import csv

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
    return rows

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

def get_priority_student(records):
    for r in records:
        if r[4] == 1:
            return r[3]
    return "None 🎉"

# ================= AUTH =================
def auth_page(title, link):
    return f"""
    <html>
    <head>
    <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600&display=swap" rel="stylesheet">
    <style>
    body{{font-family:'Fredoka';background:#eef2ff;display:flex;justify-content:center;align-items:center;height:100vh;}}
    .card{{background:white;padding:30px;border-radius:20px;width:320px;box-shadow:0 10px 25px rgba(0,0,0,.1);text-align:center;}}
    input{{width:100%;padding:12px;margin:10px 0;border-radius:14px;border:2px solid #ddd;}}
    button{{width:100%;padding:12px;border:none;border-radius:14px;background:#6366f1;color:white;}}
    </style>
    </head>
    <body>
    <div class="card">
    <h2>{title}</h2>
    <form method="post">
    <input name="username" required>
    <input name="password" type="password" required>
    <button>{title}</button>
    </form>
    {link}
    </div>
    </body>
    </html>
    """

@app.get("/login", response_class=HTMLResponse)
def login_page():
    return auth_page("Login", '<a href="/signup">Create account</a>')

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

@app.get("/signup", response_class=HTMLResponse)
def signup_page():
    return auth_page("Sign Up", '<a href="/login">Back</a>')

@app.post("/signup")
def signup(username: str = Form(...), password: str = Form(...)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users VALUES (NULL,?,?)",
                   (username, hash_pw(password)))
    conn.commit()
    conn.close()
    return RedirectResponse("/login",303)

@app.get("/logout")
def logout():
    res = RedirectResponse("/login",303)
    res.delete_cookie("user_id")
    return res

# ================= EXPORT =================
@app.get("/export")
def export(request: Request):
    user_id = request.cookies.get("user_id")
    records = load_records(user_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date","Homework","Student","Priority"])

    for r in records:
        writer.writerow([r[1], r[2], r[3], r[4]])

    output.seek(0)

    return StreamingResponse(output, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=data.csv"})

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
    priority_count = len([r for r in records if r[4]])

    priority_student = get_priority_student(records)

    rows = "".join(f"""
    <tr>
    <td>{r[1]}</td>
    <td>{r[2]}</td>
    <td>{r[3]}</td>
    <td>
    <form action="/delete/{r[0]}" method="post">
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
body{{font-family:'Fredoka';background:#f5f3ff;padding:30px;}}
.container{{max-width:1100px;margin:auto;}}

.card{{
background:white;
padding:25px;
border-radius:20px;
margin-bottom:30px;
box-shadow:0 10px 25px rgba(0,0,0,.08);
}}

.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;}}

.big{{font-size:28px;color:#6366f1;}}

input{{width:100%;padding:12px;margin:10px 0;border-radius:14px;border:2px solid #ddd;}}

button{{border:none;border-radius:12px;padding:10px 16px;background:#6366f1;color:white;cursor:pointer;}}
.delete{{background:#ef4444;}}

.header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;}}

/* FIXED CHECKBOX ALIGN */
.checkbox-row {{
display:flex;
align-items:center;
gap:8px;
margin-top:10px;
}}

.table-header {{
background:linear-gradient(90deg,#6366f1,#8b5cf6);
color:white;
padding:15px;
border-radius:16px;
display:flex;
justify-content:space-between;
align-items:center;
margin-bottom:10px;
}}

table{{width:100%;border-collapse:collapse;}}
th,td{{padding:12px;text-align:left;}}
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
<input name="homework" placeholder="Homework" required>
<input name="student" placeholder="Student" required>

<div class="checkbox-row">
<input type="checkbox" name="priority" id="priority">
<label for="priority">Priority</label>
</div>

<br>
<button>Add ✨</button>
</form>
</div>

<div class="card">
<h3>Priority Student</h3>
<b>{priority_student}</b>
</div>

<div class="card">
<div class="table-header">
<h3 style="margin:0;">Records</h3>
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
    user_id = request.cookies.get("user_id")

    if not homework or not student:
        return RedirectResponse("/",303)

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
