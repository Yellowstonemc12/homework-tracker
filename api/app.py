from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
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
        level TEXT,
        subject TEXT,
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
        "ID":r[0],
        "Date":r[1],
        "Homework":r[2],
        "Student":r[3],
        "Priority":r[4]
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

def get_priority_student(records):
    priority_students = [r["Student"] for r in records if r["Priority"]]
    return priority_students[0] if priority_students else "None 🎉"

# ================= AUTH =================
def auth_page(title, link):
    return f"""
    <html>
    <head>
    <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600&display=swap" rel="stylesheet">
    <style>
    body {{
        font-family:'Fredoka';
        background:#eef2ff;
        display:flex;
        justify-content:center;
        align-items:center;
        height:100vh;
    }}
    .card {{
        background:white;
        padding:30px;
        border-radius:20px;
        width:320px;
        text-align:center;
    }}
    input {{
        width:100%;
        padding:12px;
        margin:10px 0;
        border-radius:14px;
        border:2px solid #ddd;
    }}
    button {{
        width:100%;
        padding:12px;
        border:none;
        border-radius:14px;
        background:#6366f1;
        color:white;
    }}
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
        res.set_cookie("user_id", str(user[0]), httponly=True)
        return res

    return RedirectResponse("/login",303)

@app.get("/signup", response_class=HTMLResponse)
def signup_page():
    return auth_page("Sign Up", '<a href="/login">Back to login</a>')

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
    priority_student = get_priority_student(records)

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
body {{
    font-family:'Fredoka';
    background:linear-gradient(135deg,#eef2ff,#fdf4ff);
    padding:30px;
}}

.container {{
    max-width:1100px;
    margin:auto;
}}

.header {{
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-bottom:20px;
}}

.logout-btn {{
    padding:10px 16px;
    border-radius:12px;
    background:#6366f1;
    color:white;
    border:none;
}}

.grid {{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:20px;
}}

.card {{
    background:white;
    padding:20px;
    border-radius:20px;
}}

.big {{
    font-size:28px;
    color:#6366f1;
}}

input {{
    width:100%;
    padding:12px;
    border-radius:14px;
    border:2px solid #ddd;
    margin:6px 0;
}}

button {{
    border-radius:12px;
    padding:10px 14px;
    border:none;
    background:#6366f1;
    color:white;
    cursor:pointer;
}}

.delete {{
    background:#ef4444;
}}

.checkbox {{
    display:flex;
    align-items:center;
    gap:8px;
    margin-top:10px;
}}

.records-header {{
    background:#6366f1;
    color:white;
    padding:16px;
    border-radius:16px 16px 0 0;
    display:flex;
    justify-content:space-between;
    align-items:center;
}}

.table-box {{
    background:white;
    border-radius:0 0 16px 16px;
    padding:10px;
}}

table {{
    width:100%;
    border-collapse:collapse;
}}

th {{
    position:sticky;
    top:0;
    background:#6366f1;
    color:white;
    padding:10px;
}}

td {{
    padding:10px;
    border-bottom:1px solid #eee;
}}

tr:hover {{
    background:#f9fafb;
}}
</style>
</head>

<body>
<div class="container">

<div class="header">
<h1>📚 Homework Tracker</h1>
<a href="/logout"><button class="logout-btn">Logout</button></a>
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

<div class="checkbox">
<input type="checkbox" name="priority">
<label>Priority</label>
</div>

<br>
<button>Add ✨</button>
</form>
</div>

<div class="card">
<h3>Priority Student</h3>
<b>{priority_student}</b>
</div>

<div class="card" style="padding:0; overflow:hidden;">
<div class="records-header">
<h3>Records</h3>
<a href="/export"><button style="background:white;color:#6366f1;">Export</button></a>
</div>

<div class="table-box">
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

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO homework VALUES (NULL,?,?,?,?,?,?,?)
    """,(user_id,
        datetime.now().strftime("%Y-%m-%d"),
        "", "",  # removed level & subject
        homework,
        student,
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
