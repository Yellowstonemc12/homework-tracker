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

    total = len(records)
    unique = len(counts)
    priority_list = [r for r in records if r["Priority"]]

    error = request.query_params.get("error")

    rows = "".join(f"""
    <tr class="row">
    <td>{r['Date']}</td>
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
    <div class="pill">{r['Student']} • {r['Homework']}</div>
    """ for r in priority_list)

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

.card{{
background:white;
padding:20px;
border-radius:20px;
margin-bottom:20px;
box-shadow:0 8px 20px rgba(0,0,0,.08);
transition:.2s;
}}
.card:hover{{transform:translateY(-5px);}}

.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;}}

.big{{font-size:28px;color:#6366f1;}}

input{{border-radius:14px;padding:10px;border:2px solid #ddd;width:100%;margin:6px 0;}}

button{{border-radius:12px;padding:8px 12px;border:none;background:#6366f1;color:white;cursor:pointer;}}

.delete{{background:#ef4444;}}

.badge{{background:#ef4444;color:white;padding:4px 8px;border-radius:999px;margin-left:6px;}}

/* RECORD HEADER */
.records-header{{
background:#6366f1;
color:white;
padding:14px;
border-radius:16px;
display:flex;
justify-content:space-between;
}}

/* TABLE */
table{{width:100%;border-collapse:collapse;}}
th{{padding:10px;text-align:left;background:#6366f1;color:white;}}
td{{padding:10px;border-bottom:1px solid #eee;}}

/* ROW ANIMATION */
.row{{transition:.2s;}}
.row:hover{{background:#f3f4ff;}}

/* PRIORITY */
.pill{{
background:#fef3c7;
padding:8px 12px;
border-radius:999px;
display:inline-block;
margin:5px;
}}

/* ERROR POPUP */
.error{{
background:#fecaca;
padding:10px;
border-radius:12px;
margin-bottom:15px;
}}
</style>
</head>
<body>
<div class="container">

<h1>📚 Homework Tracker</h1>
<a href="/logout"><button>Logout</button></a>

<div class="grid">
<div class="card">Total<div class="big">{total}</div></div>
<div class="card">Students<div class="big">{unique}</div></div>
<div class="card">Priority<div class="big">{len(priority_list)}</div></div>
</div>

{"<div class='error'>⚠ Please fill in all fields</div>" if error else ""}

<div class="card">
<h3>Add Record</h3>
<form method="post" action="/add">
<input name="homework" placeholder="Homework">
<input name="student" placeholder="Student">

<label style="display:flex;align-items:center;gap:8px;justify-content:flex-start;">
<input type="checkbox" name="priority" style="width:auto;">
<span>Priority</span>
</label>

<br>
<button>Add ✨</button>
</form>
</div>

<div class="card">
<h3>Priority Students</h3>
{priority_rows if priority_rows else "None 🎉"}
</div>

<div class="card">
<div class="records-header">
<h3>Records</h3>
<a href="/export"><button style="background:white;color:#6366f1;">Export</button></a>
</div>
<table>
<tr>
<th>Date</th><th>Homework</th><th>Student</th><th>Action</th>
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
homework: str = Form(""),
student: str = Form(""),
priority: str = Form(None)):

    if not homework or not student:
        return RedirectResponse("/?error=1",303)

    user_id = request.cookies.get("user_id")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO homework VALUES (NULL,?,?,?,?,?,?,?)
    """,(user_id,
        datetime.now().strftime("%Y-%m-%d"),
        "", "", homework, student,
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
