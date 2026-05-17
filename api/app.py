from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
import sqlite3
from datetime import datetime

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

# ================= AUTH UI =================
def auth_page(title, link):
    return f"""
    <html>
    <head>
    <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600&display=swap" rel="stylesheet">
    <style>
    *{{font-family:'Fredoka';}}
    body{{
        background:#eef2ff;
        display:flex;
        justify-content:center;
        align-items:center;
        height:100vh;
    }}
    .card{{
        background:white;
        padding:30px;
        border-radius:20px;
        width:320px;
        box-shadow:0 10px 25px rgba(0,0,0,0.1);
        text-align:center;
    }}
    input{{
        width:100%;
        padding:12px;
        margin:10px 0;
        border-radius:12px;
        border:2px solid #ddd;
    }}
    button{{
        width:100%;
        padding:12px;
        border:none;
        border-radius:12px;
        background:#6366f1;
        color:white;
        cursor:pointer;
    }}
    a{{display:block;margin-top:12px;}}
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
    cursor.execute("SELECT id FROM users WHERE username=? AND password=?",(username,password))
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
    cursor.execute("INSERT INTO users (username,password) VALUES (?,?)",(username,password))
    conn.commit()
    conn.close()
    return RedirectResponse("/login",303)

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
    <td>
        {r['Student']}
        {"<span class='priority'>★</span>" if r['Priority'] else ""}
        <span class="badge">{counts.get(r['Student'],0)}</span>
    </td>
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
--bg:#f8fafc;
--card:#ffffff;
--text:#222;
--accent:#6366f1;
}}

.dark {{
--bg:#0f172a;
--card:#1e293b;
--text:#e2e8f0;
}}

body {{
background:var(--bg);
color:var(--text);
padding:30px;
transition:.3s;
}}

.container {{max-width:1100px;margin:auto;}}

.title {{
font-size:42px;
display:flex;
align-items:center;
gap:10px;
}}

.settings-btn {{
margin-left:auto;
cursor:pointer;
font-size:22px;
}}

.card {{
background:var(--card);
padding:22px;
border-radius:20px;
margin-bottom:20px;
box-shadow:0 8px 20px rgba(0,0,0,0.08);
}}

.grid {{
display:grid;
grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
gap:20px;
}}

.big {{font-size:30px;color:var(--accent);}}

/* inputs */
input {{
width:100%;
padding:12px;
border-radius:12px;
border:2px solid #ddd;
margin:6px 0;
}}

input:focus {{
border-color:var(--accent);
outline:none;
}}

button {{
padding:10px 16px;
border-radius:12px;
border:none;
background:var(--accent);
color:white;
cursor:pointer;
}}

.delete {{background:#ef4444;}}

.badge {{
background:#ef4444;
color:white;
padding:4px 8px;
border-radius:999px;
margin-left:6px;
}}

.priority {{
background:gold;
padding:4px 8px;
border-radius:999px;
margin-left:5px;
}}

table {{
width:100%;
border-collapse:collapse;
margin-top:10px;
}}

th {{
background:var(--accent);
color:white;
padding:10px;
}}

td {{
padding:10px;
border-bottom:1px solid #eee;
}}

#settingsPanel {{
position:fixed;
top:0;
right:-300px;
width:280px;
height:100%;
background:var(--card);
box-shadow:-5px 0 20px rgba(0,0,0,0.15);
padding:20px;
transition:.3s;
z-index:999;
}}

#settingsPanel.open {{right:0;}}

.color {{
padding:10px;
border-radius:10px;
margin-top:8px;
cursor:pointer;
color:white;
text-align:center;
}}
</style>
</head>

<body>

<div id="settingsPanel">
<h3>⚙ Settings</h3>
<button onclick="toggleDark()">🌙 Dark Mode</button>

<div class="color" style="background:#6366f1" onclick="setColor('#6366f1')">Indigo</div>
<div class="color" style="background:#22c55e" onclick="setColor('#22c55e')">Green</div>
<div class="color" style="background:#ef4444" onclick="setColor('#ef4444')">Red</div>
<div class="color" style="background:#f59e0b" onclick="setColor('#f59e0b')">Orange</div>
</div>

<div class="container">

<div class="title">
📚 Homework Tracker
<span class="settings-btn" onclick="toggleSettings()">⚙</span>
</div>

<div class="grid">
<div class="card">📊<div class="big">{total}</div></div>
<div class="card">👥<div class="big">{unique}</div></div>
<div class="card">⭐<div class="big">{priority_count}</div></div>
</div>

<div class="card">
<h3>Add Record</h3>
<form method="post" action="/add">
<input name="level" placeholder="Level" required>
<input name="subject" placeholder="Subject" required>
<input name="homework" placeholder="Homework" required>
<input name="student" placeholder="Student" required>
<label><input type="checkbox" name="priority"> Priority</label>
<br><br>
<button>Add ✨</button>
</form>
</div>

<div class="card">
<h3>Records</h3>
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

<script>
function toggleSettings(){{
document.getElementById("settingsPanel").classList.toggle("open");
}}

function toggleDark(){{
document.body.classList.toggle("dark");
localStorage.setItem("dark", document.body.classList.contains("dark"));
}}

function setColor(c){{
document.documentElement.style.setProperty('--accent',c);
localStorage.setItem("theme",c);
}}

if(localStorage.getItem("dark")==="true"){{
document.body.classList.add("dark");
}}

if(localStorage.getItem("theme")){{
document.documentElement.style.setProperty('--accent',localStorage.getItem("theme"));
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
