from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
import sqlite3
from datetime import datetime
import csv
from io import StringIO

app = FastAPI()
DB_PATH = "/tmp/homework.db"

# ================= DATABASE =================
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

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
        SELECT id, date, level, subject, homework, student, priority
        FROM homework
        WHERE user_id=?
        ORDER BY priority DESC, id DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()

    return [{
        "ID": r[0], "Date": r[1], "Level": r[2],
        "Subject": r[3], "Homework": r[4],
        "Student": r[5], "Priority": r[6],
    } for r in rows]

def get_counts(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT student, COUNT(*)
        FROM homework
        WHERE user_id=?
        GROUP BY student
    """, (user_id,))
    data = dict(cursor.fetchall())
    conn.close()
    return data

# ================= AUTH PAGES =================
def auth_page(title, action):
    return f"""
    <html>
    <head>
    <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600&display=swap" rel="stylesheet">
    <style>
    * {{ font-family:'Fredoka', sans-serif; }}
    body {{
        background:#f5f7fb;
        display:flex;
        align-items:center;
        justify-content:center;
        height:100vh;
    }}
    .card {{
        background:white;
        padding:30px;
        border-radius:20px;
        width:300px;
        box-shadow:0 10px 25px rgba(0,0,0,0.1);
        text-align:center;
    }}
    input {{
        width:100%;
        padding:10px;
        margin:8px 0;
        border-radius:10px;
        border:2px solid #ddd;
    }}
    button {{
        width:100%;
        padding:10px;
        border:none;
        border-radius:10px;
        background:#4f46e5;
        color:white;
        cursor:pointer;
    }}
    a {{ display:block; margin-top:10px; }}
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
    {action}
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
                   (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        res = RedirectResponse("/", status_code=303)
        res.set_cookie("user_id", str(user[0]))
        return res
    return RedirectResponse("/login", status_code=303)

@app.get("/signup", response_class=HTMLResponse)
def signup_page():
    return auth_page("Sign Up", '<a href="/login">Back to login</a>')

@app.post("/signup")
def signup(username: str = Form(...), password: str = Form(...)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username,password) VALUES (?,?)",
                   (username, password))
    conn.commit()
    conn.close()
    return RedirectResponse("/login", status_code=303)

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

    rows = "".join(f"""
    <tr>
    <td>{r['Date']}</td>
    <td>{r['Level']}</td>
    <td>{r['Subject']}</td>
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

:root {{
--bg:#f5f7fb;
--card:#fff;
--accent:#4f46e5;
}}

.dark {{
--bg:#0f172a;
--card:#1e293b;
}}

body {{
background:var(--bg);
padding:30px;
}}

.container {{max-width:1100px;margin:auto;}}

.card {{
background:var(--card);
padding:20px;
border-radius:20px;
margin-bottom:20px;
}}

.grid {{
display:grid;
grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
gap:20px;
}}

.big {{font-size:28px;color:var(--accent);}}

/* SETTINGS */
#settingsPanel {{
position:fixed;
top:0;
right:-280px;
width:260px;
height:100%;
background:white;
padding:20px;
transition:.3s;
box-shadow:-5px 0 20px rgba(0,0,0,.2);
z-index:999;
}}
#settingsPanel.open {{right:0;}}

.color {{
padding:10px;
border-radius:10px;
margin:5px 0;
cursor:pointer;
color:white;
text-align:center;
}}

</style>
</head>

<body>

<div id="settingsPanel">
<h3>Settings</h3>
<button onclick="toggleDark()">Dark Mode</button>
<div class="color" style="background:#4f46e5" onclick="setColor('#4f46e5')">Blue</div>
<div class="color" style="background:#16a34a" onclick="setColor('#16a34a')">Green</div>
<div class="color" style="background:#dc2626" onclick="setColor('#dc2626')">Red</div>
</div>

<div class="container">

<h1>Homework Tracker ⚙ <span onclick="toggleSettings()">⚙</span></h1>

<div class="grid">
<div class="card">Total<div class="big">{total}</div></div>
<div class="card">Students<div class="big">{unique}</div></div>
<div class="card">Priority<div class="big">{priority_count}</div></div>
</div>

<div class="card">
<form method="post" action="/add">
<input name="level" placeholder="Level">
<input name="subject" placeholder="Subject">
<input name="homework" placeholder="Homework">
<input name="student" placeholder="Student">
<label><input type="checkbox" name="priority"> Priority</label>
<button>Add</button>
</form>
</div>

<div class="card">
<table>
<tr>
<th>Date</th><th>Level</th><th>Subject</th><th>Homework</th><th>Student</th><th>Action</th>
</tr>
{rows}
</table>
</div>

</div>

<script>
function toggleSettings(){{
document.getElementById("settingsPanel").classList.toggle("open");
}}
function toggleDark(){{
document.body.classList.toggle("dark");
}}
function setColor(c){{
document.documentElement.style.setProperty('--accent',c);
}}
</script>

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
    INSERT INTO homework (user_id,date,level,subject,homework,student,priority)
    VALUES (?,?,?,?,?,?,?)
    """,(
        user_id,
        datetime.now().strftime("%Y-%m-%d"),
        level,subject,homework,student,
        1 if priority else 0
    ))

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
