from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
import sqlite3
from datetime import datetime
import hashlib
import csv
from io import StringIO

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
    SELECT id,date,level,subject,homework,student,priority
    FROM homework
    WHERE user_id=?
    ORDER BY priority DESC,id DESC
    """,(user_id,))

    rows = cursor.fetchall()
    conn.close()

    return [{
        "ID":r[0],"Date":r[1],"Level":r[2],
        "Subject":r[3],"Homework":r[4],
        "Student":r[5],"Priority":r[6]
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

def get_priority(records):
    return [r for r in records if r["Priority"]]

# ================= AUTH =================
def auth_page(title, link):
    return f"""
    <html>
    <head>
    <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600&display=swap" rel="stylesheet">
    <style>
    *{{font-family:'Fredoka';}}
    body{{background:#eef2ff;display:flex;justify-content:center;align-items:center;height:100vh;}}
    .card{{background:white;padding:30px;border-radius:20px;width:320px;
    box-shadow:0 10px 25px rgba(0,0,0,.1);text-align:center;}}
    input{{width:100%;padding:12px;margin:10px 0;border-radius:14px;border:2px solid #ddd;}}
    button{{width:100%;padding:12px;border:none;border-radius:14px;background:#4f46e5;color:white;}}
    </style>
    </head>
    <body>
    <div class="card">
    <h2>{title}</h2>
    <form method="post">
    <input name="username" placeholder="Username" required>
    <input name="password" type="password" placeholder="Password" required>
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
    priority = get_priority(records)

    total = len(records)
    unique = len(counts)
    priority_count = len(priority)

    rows = "".join(f"""
    <tr>
    <td>{r['Date']}</td>
    <td>{r['Level']}</td>
    <td>{r['Subject']}</td>
    <td>{r['Homework']}</td>
    <td>{r['Student']} <span class="badge">{counts.get(r['Student'],0)}</span></td>
    <td>
    <form action="/delete/{r['ID']}" method="post">
    <button class="delete">✕</button>
    </form>
    </td>
    </tr>
    """ for r in records)

    priority_rows = "".join(f"""
    <tr>
    <td>{r['Student']}</td>
    <td>{r['Homework']}</td>
    <td>{r['Subject']}</td>
    </tr>
    """ for r in priority)

    return f"""
<html>
<head>
<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600&display=swap" rel="stylesheet">
<style>
*{{font-family:'Fredoka',sans-serif;box-sizing:border-box;}}

:root{{
--bg:#f5f7fb;
--card:#ffffff;
--accent:#4f46e5;
--text:#222;
}}

body{{
background:var(--bg);
color:var(--text);
padding:30px;
}}

.container{{max-width:1100px;margin:auto;}}

.card{{
background:var(--card);
padding:22px;
border-radius:20px;
margin-bottom:20px;
box-shadow:0 8px 20px rgba(0,0,0,0.08);
transition:0.2s;
}}

.card:hover{{transform:translateY(-3px);}}

.grid{{
display:grid;
grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
gap:20px;
}}

.big{{font-size:30px;color:var(--accent);}}

input{{
padding:12px;
border-radius:12px;
border:2px solid #ddd;
margin:6px 0;
width:100%;
}}

button{{
padding:10px 16px;
border-radius:12px;
border:none;
background:var(--accent);
color:white;
cursor:pointer;
}}

.delete{{background:#ef4444;}}

.badge{{
background:#ef4444;
color:white;
padding:4px 8px;
border-radius:999px;
margin-left:6px;
}}

table{{width:100%;border-collapse:collapse;}}

th{{
background:var(--accent);
color:white;
padding:10px;
position:sticky;
top:0;
}}

td{{
padding:10px;
border-bottom:1px solid #eee;
}}

tr:hover{{background:rgba(0,0,0,0.05);}}

label{{
display:flex;
align-items:center;
gap:6px;
margin-top:8px;
}}
</style>
</head>

<body>

<div class="container">

<div style="display:flex;justify-content:space-between;align-items:center;">
<h1>Homework Tracker</h1>
<a href="/logout"><button>Logout</button></a>
</div>

<div class="grid">
<div class="card">Total<div class="big">{total}</div></div>
<div class="card">Students<div class="big">{unique}</div></div>
<div class="card">Priority<div class="big">{priority_count}</div></div>
</div>

<div class="card">
<h3>Priority Students</h3>
{f"<table><tr><th>Student</th><th>Homework</th><th>Subject</th></tr>{priority_rows}</table>" if priority else "None 🎉"}
</div>

<div class="card">
<h3>Add Record</h3>
<form method="post" action="/add">
<input name="level" placeholder="Level">
<input name="subject" placeholder="Subject">
<input name="homework" placeholder="Homework">
<input name="student" placeholder="Student">
<label>
<input type="checkbox" name="priority"> Priority
</label>
<br><br>
<button>Add</button>
</form>
</div>

<div class="card">

<div style="
background:var(--accent);
color:white;
padding:14px 18px;
border-radius:16px;
display:flex;
justify-content:space-between;
align-items:center;
margin-bottom:15px;
">
<h3 style="margin:0;">Records</h3>

<a href="/export">
<button style="background:white;color:var(--accent);font-weight:bold;">
Export CSV
</button>
</a>

</div>

<div style="background:#f9fafb;border-radius:16px;padding:10px;overflow-x:auto;max-height:400px;">

<table>
<tr>
<th>Date</th>
<th>Level</th>
<th>Subject</th>
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
level: str = Form(...),
subject: str = Form(...),
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
        level,subject,homework,student,
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

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["Date","Level","Subject","Homework","Student","Priority"])

    for r in records:
        writer.writerow([
            r["Date"],
            r["Level"],
            r["Subject"],
            r["Homework"],
            r["Student"],
            r["Priority"]
        ])

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition":"attachment; filename=homework.csv"}
    )
