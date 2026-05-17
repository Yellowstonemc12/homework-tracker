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

    # USERS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # HOMEWORK
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

    return [
        {
            "ID": r[0],
            "Date": r[1],
            "Level": r[2],
            "Subject": r[3],
            "Homework": r[4],
            "Student": r[5],
            "Priority": r[6],
        }
        for r in rows
    ]

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

def get_top_student(counts):
    if not counts:
        return ("None", 0)
    top = max(counts, key=counts.get)
    return (top, counts[top])

# ================= AUTH =================
@app.get("/login", response_class=HTMLResponse)
def login_page():
    return """
    <h2>Login</h2>
    <form method="post">
        <input name="username" placeholder="Username"><br>
        <input name="password" type="password" placeholder="Password"><br>
        <button>Login</button>
    </form>
    <a href="/signup">Sign up</a>
    """

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE username=? AND password=?",
        (username, password)
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        response = RedirectResponse("/", status_code=303)
        response.set_cookie("user_id", str(user[0]))
        return response

    return RedirectResponse("/login", status_code=303)

@app.get("/signup", response_class=HTMLResponse)
def signup_page():
    return """
    <h2>Sign Up</h2>
    <form method="post">
        <input name="username"><br>
        <input name="password" type="password"><br>
        <button>Create</button>
    </form>
    """

@app.post("/signup")
def signup(username: str = Form(...), password: str = Form(...)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, password)
    )

    conn.commit()
    conn.close()

    return RedirectResponse("/login", status_code=303)

# ================= MAIN PAGE =================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    records = load_records(user_id)
    counts = get_counts(user_id)

    total = len(records)
    unique = len(counts)
    priority_count = len([r for r in records if r["Priority"]])
    top_student, top_missing = get_top_student(counts)

    priority_rows = "".join(f"""
    <tr>
        <td>{r['Student']}</td>
        <td>{r['Homework']}</td>
        <td>{r['Subject']}</td>
        <td><span class="priority">★</span></td>
    </tr>
    """ for r in records if r["Priority"])

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
<!DOCTYPE html>
<html>
<head>
<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600&display=swap" rel="stylesheet">
<style>
* {{
    font-family: 'Fredoka', sans-serif;
    box-sizing: border-box;
}}

:root {{
    --bg: #f5f7fb;
    --card: #ffffff;
    --text: #222;
    --accent: #4f46e5;
}}

.dark {{
    --bg: #0f172a;
    --card: #1e293b;
    --text: #e2e8f0;
}}

body {{
    background: var(--bg);
    color: var(--text);
    padding: 30px;
}}

.container {{
    max-width: 1100px;
    margin: auto;
}}

.title {{
    font-size: 42px;
    display: flex;
    align-items: center;
}}

.settings-btn {{
    margin-left: auto;
    cursor: pointer;
}}

.card {{
    background: var(--card);
    padding: 20px;
    border-radius: 18px;
    margin-bottom: 20px;
}}

.grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px,1fr));
    gap: 20px;
}}

.big {{
    font-size: 28px;
    color: var(--accent);
}}

input {{
    padding: 10px;
    border-radius: 10px;
    border: 2px solid #ddd;
    width: 100%;
}}

button {{
    padding: 10px;
    border-radius: 10px;
    background: var(--accent);
    color: white;
    border: none;
}}

.delete {{
    background: red;
}}

.badge {{
    background: red;
    color: white;
    padding: 4px 8px;
    border-radius: 999px;
}}

.priority {{
    background: gold;
    padding: 4px 8px;
    border-radius: 999px;
}}

#settingsPanel {{
    position: fixed;
    top: 0;
    right: -300px;
    width: 260px;
    height: 100%;
    background: var(--card);
    padding: 20px;
    transition: 0.3s;
}}

#settingsPanel.open {{
    right: 0;
}}
</style>
</head>

<body>

<div id="settingsPanel">
<h3>⚙ Settings</h3>
<button onclick="toggleDark()">Dark Mode</button>
<br><br>
<div onclick="setColor('#4f46e5')">Blue</div>
<div onclick="setColor('#16a34a')">Green</div>
<div onclick="setColor('#dc2626')">Red</div>
</div>

<div class="container">

<div class="title">
📚 Homework Tracker
<span class="settings-btn" onclick="toggleSettings()">⚙</span>
</div>

<div class="grid">
<div class="card">Total<div class="big">{total}</div></div>
<div class="card">Students<div class="big">{unique}</div></div>
<div class="card">Priority<div class="big">{priority_count}</div></div>
<div class="card">{top_student}<br>{top_missing}</div>
</div>

<div class="card">
<form action="/add" method="post">
<input name="level" placeholder="Level">
<input name="subject" placeholder="Subject">
<input name="homework" placeholder="Homework">
<input name="student" placeholder="Student">
<label><input type="checkbox" name="priority"> Priority</label>
<button>Add</button>
</form>
</div>

<div class="card">
<h3>Records</h3>
<input id="search" onkeyup="search()" placeholder="Search">
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
document.documentElement.style.setProperty('--accent', c);
}}
function search(){{
let input=document.getElementById("search").value.toLowerCase();
document.querySelectorAll("table tr").forEach((r,i)=>{{
if(i===0)return;
r.style.display=r.innerText.toLowerCase().includes(input)?"":"none";
}});
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
    priority: str = Form(None)
):
    user_id = request.cookies.get("user_id")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO homework (user_id, date, level, subject, homework, student, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        datetime.now().strftime("%Y-%m-%d"),
        level, subject, homework, student,
        1 if priority else 0
    ))

    conn.commit()
    conn.close()

    return RedirectResponse("/", status_code=303)

# ================= DELETE =================
@app.post("/delete/{record_id}")
def delete(request: Request, record_id: int):
    user_id = request.cookies.get("user_id")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM homework WHERE id=? AND user_id=?",
        (record_id, user_id)
    )

    conn.commit()
    conn.close()

    return RedirectResponse("/", status_code=303)

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
            r["Date"], r["Level"], r["Subject"],
            r["Homework"], r["Student"], r["Priority"]
        ])

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=homework.csv"}
    )
