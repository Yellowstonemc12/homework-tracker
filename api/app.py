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
def load_records():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id,date,level,subject,homework,student,priority
    FROM homework
    ORDER BY priority DESC,id DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    return [{
        "ID":r[0],"Date":r[1],"Level":r[2],
        "Subject":r[3],"Homework":r[4],
        "Student":r[5],"Priority":r[6]
    } for r in rows]

def get_counts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT student,COUNT(*) FROM homework GROUP BY student")
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
    body{{font-family:Fredoka;background:#fdf2ff;
    display:flex;justify-content:center;align-items:center;height:100vh;}}
    .card{{background:white;padding:30px;border-radius:24px;width:320px;
    box-shadow:0 10px 25px rgba(0,0,0,.1);text-align:center;}}
    input{{width:100%;padding:12px;margin:10px 0;border-radius:14px;border:2px solid #ddd;}}
    button{{width:100%;padding:12px;border:none;border-radius:14px;
    background:#a78bfa;color:white;}}
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
        res.set_cookie("user_id", str(user[0]), max_age=60*60*24*7)
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

    if not request.cookies.get("user_id"):
        return RedirectResponse("/login")

    records = load_records()
    counts = get_counts()

    rows = "".join(f"""
    <tr>
    <td>{r['Date']}</td>
    <td>{r['Level']}</td>
    <td>{r['Subject']}</td>
    <td>{r['Homework']}</td>
    <td>{r['Student']}</td>
    <td>
        <a href="/edit/{r['ID']}"><button>✏</button></a>
        <form action="/delete/{r['ID']}" method="post" style="display:inline;">
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
body{{font-family:Fredoka;background:#fdf2ff;padding:30px;}}
.card{{background:white;padding:20px;border-radius:20px;margin-bottom:20px;}}

/* sparkle */
.sparkle {{
position: fixed;
width: 6px;
height: 6px;
background: pink;
border-radius: 50%;
animation: pop 0.6s ease forwards;
}}
@keyframes pop {{
to {{transform:translateY(-40px);opacity:0;}}
}}
</style>
</head>

<body>

<h1>
<img src="https://api.iconify.design/ph:book-open-fill.svg?color=%23a78bfa" width="28">
Homework Tracker
</h1>

<a href="/logout"><button>Logout</button></a>

<div class="card">
<h3>Add Record</h3>
<form method="post" action="/add" onsubmit="sparkle(event)">
<input name="level" placeholder="Level">
<input name="subject" placeholder="Subject">
<input name="homework" placeholder="Homework">
<input name="student" placeholder="Student">
<label><input type="checkbox" name="priority"> Priority</label>
<br><br>
<button>Add</button>
</form>
</div>

<div class="card">
<h3>Records</h3>
<table>
<tr>
<th>Date</th><th>Level</th><th>Subject</th>
<th>Homework</th><th>Student</th><th>Action</th>
</tr>
{rows}
</table>
</div>

<script>
function sparkle(e){{
for(let i=0;i<10;i++){{
let s=document.createElement('div');
s.className='sparkle';
s.style.left=event.clientX+'px';
s.style.top=event.clientY+'px';
document.body.appendChild(s);
setTimeout(()=>s.remove(),600);
}}
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

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO homework VALUES (NULL,?,?,?,?,?,?,?)
    """,(request.cookies.get("user_id"),
        datetime.now().strftime("%Y-%m-%d"),
        level,subject,homework,student,
        1 if priority else 0))
    conn.commit()
    conn.close()

    return RedirectResponse("/",303)

# ================= DELETE =================
@app.post("/delete/{id}")
def delete(id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM homework WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/",303)

# ================= EDIT =================
@app.get("/edit/{id}", response_class=HTMLResponse)
def edit_page(id: int):
    return f"""
    <form method="post">
    <input name="level" placeholder="Level">
    <input name="subject" placeholder="Subject">
    <input name="homework" placeholder="Homework">
    <input name="student" placeholder="Student">
    <button>Save</button>
    </form>
    """

@app.post("/edit/{id}")
def edit(id: int,
level: str = Form(...),
subject: str = Form(...),
homework: str = Form(...),
student: str = Form(...)):

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE homework
    SET level=?, subject=?, homework=?, student=?
    WHERE id=?
    """,(level,subject,homework,student,id))
    conn.commit()
    conn.close()

    return RedirectResponse("/",303)
