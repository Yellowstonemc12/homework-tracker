from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
from datetime import datetime
import hashlib
import json

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
    ORDER BY id ASC
    """,(user_id,))
    rows = cursor.fetchall()
    conn.close()

    return [{
        "ID":r[0],
        "Date":r[1],
        "Level":r[2],
        "Subject":r[3],
        "Homework":r[4],
        "Student":r[5],
        "Priority":r[6]
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

def get_daily_counts(records):
    counts = {}
    for r in records:
        d = r["Date"]
        counts[d] = counts.get(d, 0) + 1
    return counts

# ================= AUTH =================
def auth_page(title, link):
    return f"""
    <html>
    <head>
    <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600&display=swap" rel="stylesheet">
    <style>
    *{{font-family:'Fredoka';}}
    body{{
        background:linear-gradient(135deg,#e0e7ff,#fce7f3);
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
        box-shadow:0 10px 30px rgba(0,0,0,.15);
        text-align:center;
    }}
    input{{
        width:100%;
        padding:12px;
        margin:10px 0;
        border-radius:20px;
        border:2px solid #ddd;
    }}
    button{{
        width:100%;
        padding:12px;
        border:none;
        border-radius:20px;
        background:#6366f1;
        color:white;
        cursor:pointer;
    }}
    </style>
    </head>
    <body>
    <div class="card">
    <h2>{title}</h2>
    <form method="post">
    <input name="username" required placeholder="Username">
    <input name="password" type="password" required placeholder="Password">
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
    res = RedirectResponse("/login")
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
    daily = get_daily_counts(records)

    total = len(records)
    unique = len(counts)
    priority_count = len([r for r in records if r["Priority"]])

    # chart data
    dates = list(daily.keys())
    values = list(daily.values())

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
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600&display=swap" rel="stylesheet">
<style>
*{{font-family:'Fredoka';box-sizing:border-box;}}
:root {{
--bg:#f8fafc;
--card:#fff;
--accent:#6366f1;
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
box-shadow:0 8px 20px rgba(0,0,0,.08);
transition:.3s;
}}
.card:hover {{
transform:translateY(-5px);
box-shadow:0 12px 30px rgba(0,0,0,.15);
}}

.grid {{
display:grid;
grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
gap:20px;
}}

.big {{
font-size:28px;
color:var(--accent);
}}

input {{
width:100%;
padding:12px;
border-radius:20px;
border:2px solid #ddd;
margin:6px 0;
}}

button {{
padding:10px;
border:none;
border-radius:15px;
background:var(--accent);
color:white;
cursor:pointer;
}}

.delete {{background:#ef4444;}}

table {{
width:100%;
border-collapse:collapse;
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

/* settings */
#settingsPanel {{
position:fixed;
top:0;
right:-280px;
width:260px;
height:100%;
background:white;
padding:20px;
transition:.3s;
}}
#settingsPanel.open {{right:0;}}

</style>
</head>

<body>

<div id="settingsPanel">
<h3>Settings</h3>
<button onclick="toggleDark()">Dark</button>
<div onclick="setColor('#6366f1')">Blue</div>
<div onclick="setColor('#16a34a')">Green</div>
<div onclick="setColor('#dc2626')">Red</div>
</div>

<div class="container">

<h1>📚 Homework Tracker 
<span onclick="toggleSettings()">⚙</span>
<a href="/logout"><button>Logout</button></a>
</h1>

<div class="grid">
<div class="card">Total<div class="big">{total}</div></div>
<div class="card">Students<div class="big">{unique}</div></div>
<div class="card">Priority<div class="big">{priority_count}</div></div>
</div>

<div class="card">
<canvas id="chart"></canvas>
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
new Chart(document.getElementById('chart'), {{
type:'line',
data:{{
labels:{json.dumps(dates)},
datasets:[{{
label:'Entries per Day',
data:{json.dumps(values)},
borderColor:'#6366f1',
fill:false
}}]
}}
});

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

    cursor.execute("DELETE FROM homework WHERE id=? AND user_id=?",(id,user_id))

    conn.commit()
    conn.close()

    return RedirectResponse("/",303)
