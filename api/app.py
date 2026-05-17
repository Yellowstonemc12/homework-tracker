from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
from datetime import datetime
import hashlib
import json

app = FastAPI()
DB_PATH = "/tmp/homework.db"

# ================= DB =================
def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def init():
    db = get_db()
    c = db.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS homework(
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        date TEXT,
        level TEXT,
        subject TEXT,
        homework TEXT,
        student TEXT,
        priority INTEGER DEFAULT 0
    )
    """)

    db.commit()
    db.close()

init()

# ================= DATA =================
def get_records(user_id, shared=False):
    db = get_db()
    c = db.cursor()

    if shared:
        c.execute("SELECT * FROM homework ORDER BY priority DESC, id DESC")
    else:
        c.execute("SELECT * FROM homework WHERE user_id=? ORDER BY priority DESC, id DESC",(user_id,))

    rows = c.fetchall()
    db.close()

    return rows

def get_counts(rows):
    d = {}
    for r in rows:
        d[r[6]] = d.get(r[6],0)+1
    return d

# ================= AUTH =================
def auth_ui(title, link):
    return f"""
    <style>
    body{{background:#eef2ff;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Fredoka}}
    .card{{background:white;padding:30px;border-radius:20px;width:320px;box-shadow:0 10px 25px rgba(0,0,0,.1)}}
    input{{width:100%;padding:12px;margin:10px 0;border-radius:14px;border:2px solid #ddd}}
    button{{width:100%;padding:12px;border:none;border-radius:14px;background:#6366f1;color:white}}
    </style>

    <div class="card">
    <h2>{title}</h2>
    <form method="post">
    <input name="username" required>
    <input name="password" type="password" required>
    <button>{title}</button>
    </form>
    {link}
    </div>
    """

@app.get("/login", response_class=HTMLResponse)
def login_page():
    return auth_ui("Login", '<a href="/signup">Sign up</a>')

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    db = get_db()
    c = db.cursor()

    c.execute("SELECT id FROM users WHERE username=? AND password=?",
              (username, hash_pw(password)))
    u = c.fetchone()
    db.close()

    if u:
        r = RedirectResponse("/",303)
        r.set_cookie("user_id", str(u[0]))
        return r
    return RedirectResponse("/login",303)

@app.get("/signup", response_class=HTMLResponse)
def signup_page():
    return auth_ui("Sign Up", '<a href="/login">Login</a>')

@app.post("/signup")
def signup(username: str = Form(...), password: str = Form(...)):
    db = get_db()
    c = db.cursor()
    c.execute("INSERT INTO users VALUES(NULL,?,?)",
              (username, hash_pw(password)))
    db.commit()
    db.close()
    return RedirectResponse("/login",303)

@app.get("/logout")
def logout():
    r = RedirectResponse("/login")
    r.delete_cookie("user_id")
    return r

# ================= MAIN =================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/login")

    shared = request.cookies.get("shared") == "true"

    rows = get_records(user_id, shared)
    counts = get_counts(rows)

    total = len(rows)
    top = max(counts, key=counts.get) if counts else "None"

    # chart data
    chart_labels = list(counts.keys())
    chart_values = list(counts.values())

    table = "".join(f"""
    <tr>
    <td>{r[2]}</td>
    <td>{r[3]}</td>
    <td>{r[4]}</td>
    <td>{r[5]}</td>
    <td>{r[6]}</td>
    <td>
    <form action="/delete/{r[0]}" method="post">
    <button>✕</button>
    </form>
    </td>
    </tr>
    """ for r in rows)

    return f"""
<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600&display=swap" rel="stylesheet">

<style>
*{{font-family:Fredoka;box-sizing:border-box}}

body{{background:#f8fafc;padding:30px}}

.card{{
background:white;
padding:20px;
border-radius:20px;
margin-bottom:20px;
box-shadow:0 8px 20px rgba(0,0,0,.08);
transition:.2s;
}}

.card:hover{{transform:translateY(-5px)}}

input{{
padding:12px;
border-radius:14px;
border:2px solid #ddd;
margin:6px;
width:100%;
}}

button{{
padding:10px;
border-radius:12px;
border:none;
background:#6366f1;
color:white;
cursor:pointer;
}}

.grid{{
display:grid;
grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
gap:20px;
}}

.topbar{{display:flex;justify-content:space-between}}

svg{{width:40px}}

</style>

<div class="topbar">
<h1>
<svg viewBox="0 0 24 24"><rect width="24" height="24" fill="#fde68a"/><text x="6" y="17" font-size="12">📘</text></svg>
Homework
</h1>
<div>
<a href="/logout"><button>Logout</button></a>
<form method="post" action="/toggle">
<button>{"Shared Mode" if shared else "Personal Mode"}</button>
</form>
</div>
</div>

<div class="grid">
<div class="card">🧸 Total<div>{total}</div></div>
<div class="card">📈 Top<div>{top}</div></div>
</div>

<div class="card">
<h3>Add</h3>
<form method="post" action="/add">
<input name="level" placeholder="Level">
<input name="subject" placeholder="Subject">
<input name="homework" placeholder="Homework">
<input name="student" placeholder="Student">
<button>Add</button>
</form>
</div>

<div class="card">
<canvas id="chart"></canvas>
</div>

<div class="card">
<table width="100%">
<tr><th>Date</th><th>Level</th><th>Subject</th><th>HW</th><th>Student</th><th></th></tr>
{table}
</table>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
new Chart(document.getElementById('chart'), {{
type:'bar',
data:{{
labels:{json.dumps(chart_labels)},
datasets:[{{label:'Students',data:{json.dumps(chart_values)}}}]
}}
}})
</script>
"""

@app.post("/toggle")
def toggle(request: Request):
    shared = request.cookies.get("shared") == "true"
    r = RedirectResponse("/",303)
    r.set_cookie("shared", "false" if shared else "true")
    return r

# ================= ADD =================
@app.post("/add")
def add(request: Request,
level: str = Form(...),
subject: str = Form(...),
homework: str = Form(...),
student: str = Form(...)):

    user_id = request.cookies.get("user_id")

    db = get_db()
    c = db.cursor()

    c.execute("""
    INSERT INTO homework VALUES(NULL,?,?,?,?,?,?,0)
    """,(user_id,
        datetime.now().strftime("%Y-%m-%d"),
        level,subject,homework,student))

    db.commit()
    db.close()

    return RedirectResponse("/",303)

# ================= DELETE =================
@app.post("/delete/{id}")
def delete(id:int):
    db = get_db()
    c = db.cursor()
    c.execute("DELETE FROM homework WHERE id=?",(id,))
    db.commit()
    db.close()
    return RedirectResponse("/",303)
