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
    ORDER BY id DESC
    """,(user_id,))
    rows = cursor.fetchall()
    conn.close()

    return [{
        "ID":r[0],"Date":r[1],
        "Homework":r[2],"Student":r[3],
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
    for r in records:
        if r["Priority"]:
            return r["Student"]
    return "None"

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
*{{font-family:'Fredoka';box-sizing:border-box;}}
body{{background:#f3f4f6;padding:30px;}}
.container{{max-width:1100px;margin:auto;}}

.header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;}}

.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-bottom:20px;}}

.card{{
background:white;
padding:20px;
border-radius:20px;
box-shadow:0 6px 15px rgba(0,0,0,.08);
margin-bottom:20px;
}}

.big{{font-size:26px;color:#6366f1;}}

input{{width:100%;padding:10px;margin:6px 0;border-radius:12px;border:2px solid #ddd;}}

button{{border:none;border-radius:12px;padding:8px 14px;background:#6366f1;color:white;cursor:pointer;}}

.delete{{background:#ef4444;}}

.priority-row{{display:flex;align-items:center;gap:8px;margin-top:6px;}}

.table-box{{background:#6366f1;padding:16px;border-radius:20px;margin-top:20px;}}

.table-inner{{background:white;border-radius:14px;padding:10px;}}

table{{width:100%;border-collapse:collapse;}}

th{{padding:10px;text-align:left;background:#6366f1;color:white;position:sticky;top:0;}}

td{{padding:10px;border-bottom:1px solid #eee;}}

</style>
</head>
<body>
<div class="container">

<div class="header">
<h1>📚 Homework Tracker</h1>
<div style="display:flex;gap:10px;">
<a href="/history"><button>History</button></a>
<a href="/logout"><button>Logout</button></a>
</div>
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
<button>Add</button>
</form>
</div>

<div class="card">
<h3>Priority Student</h3>
<b>{priority_student}</b>
</div>

<div class="table-box">
<div style="display:flex;justify-content:space-between;color:white;margin-bottom:10px;">
<h3>Records</h3>
<a href="/export"><button style="background:white;color:#6366f1;">Export</button></a>
</div>

<div class="table-inner">
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

# ================= HISTORY PAGE =================
@app.get("/history", response_class=HTMLResponse)
def history(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/login")

    records = load_records(user_id)

    rows = "".join(f"""
    <tr>
    <td>{r['Date']}</td>
    <td>{r['Homework']}</td>
    <td>{r['Student']}</td>
    </tr>
    """ for r in records)

    return f"""
    <html>
    <head>
    <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600&display=swap" rel="stylesheet">
    <style>
    *{{font-family:'Fredoka';}}
    body{{background:#f3f4f6;padding:30px;}}
    .container{{max-width:900px;margin:auto;}}
    table{{width:100%;border-collapse:collapse;background:white;border-radius:12px;overflow:hidden;}}
    th{{background:#6366f1;color:white;padding:10px;}}
    td{{padding:10px;border-bottom:1px solid #eee;}}
    </style>
    </head>
    <body>
    <div class="container">
    <h1>📜 History</h1>
    <a href="/"><button>Back</button></a>
    <br><br>
    <table>
    <tr><th>Date</th><th>Homework</th><th>Student</th></tr>
    {rows}
    </table>
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
