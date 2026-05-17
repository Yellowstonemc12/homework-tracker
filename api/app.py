from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
import sqlite3
from datetime import datetime
import csv
from io import StringIO

app = FastAPI()
DB_PATH = "/tmp/homework.db"


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS homework (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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


def load_records():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, date, level, subject, homework, student, priority
        FROM homework
        ORDER BY priority DESC, id DESC
    """)

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


def get_counts():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT student, COUNT(*)
        FROM homework
        GROUP BY student
    """)

    data = dict(cursor.fetchall())
    conn.close()

    return data


def get_top_student(counts):
    if not counts:
        return ("None", 0)

    top = max(counts, key=counts.get)

    return (top, counts[top])


@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


@app.get("/", response_class=HTMLResponse)
def home():
    records = load_records()
    counts = get_counts()

    total = len(records)
    unique = len(counts)
    priority_count = len([r for r in records if r["Priority"]])
    top_student, top_missing = get_top_student(counts)

    priority_rows = "".join(
        f"""
        <tr>
            <td>{r['Student']}</td>
            <td>{r['Homework']}</td>
            <td>{r['Subject']}</td>
            <td><span class="priority">★</span></td>
        </tr>
        """
        for r in records if r["Priority"]
    )

    rows = "".join(
        f"""
        <tr>
            <td>{r['Date']}</td>
            <td>{r['Level']}</td>
            <td>{r['Subject']}</td>
            <td>{r['Homework']}</td>
            <td>
                {r['Student']}
                {"<span class='priority'>★</span>" if r['Priority'] else ""}
                <span class="badge">{counts.get(r['Student'], 0)}</span>
            </td>
            <td>
                <form action="/delete/{r['ID']}" method="post">
                    <button class="delete" type="submit">✕</button>
                </form>
            </td>
        </tr>
        """
        for r in records
    )

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Homework Tracker</title>

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
    transition: 0.3s;
    overflow-x: hidden;
}}

.container {{
    max-width: 1100px;
    margin: auto;
}}

.title {{
    font-size: 48px;
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 25px;
}}

.settings-btn {{
    margin-left: auto;
    cursor: pointer;
    font-size: 22px;
}}

.card {{
    background: var(--card);
    padding: 22px;
    border-radius: 20px;
    margin-bottom: 20px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
    transition: 0.2s;
}}

.card:hover {{
    transform: translateY(-3px);
}}

.grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px,1fr));
    gap: 20px;
}}

.big {{
    font-size: 30px;
    color: var(--accent);
}}

input[type="text"],
input:not([type]) {{
    padding: 12px;
    border-radius: 12px;
    border: 2px solid #ddd;
    margin: 6px 0;
    width: 100%;
}}

input:focus {{
    border-color: var(--accent);
    outline: none;
}}

input[type="checkbox"] {{
    width: auto;
    margin-right: 8px;
}}

.checkbox-label {{
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 8px 0;
}}

button {{
    padding: 10px 16px;
    border-radius: 12px;
    border: none;
    background: var(--accent);
    color: white;
    cursor: pointer;
    transition: 0.2s;
}}

button:hover {{
    opacity: 0.9;
}}

.delete {{
    background: #ef4444;
}}

.badge {{
    background: #ef4444;
    color: white;
    padding: 4px 8px;
    border-radius: 999px;
    margin-left: 6px;
}}

.priority {{
    background: gold;
    padding: 4px 8px;
    border-radius: 999px;
    margin-left: 5px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
}}

th {{
    background: var(--accent);
    color: white;
    padding: 10px;
}}

td {{
    padding: 10px;
    border-bottom: 1px solid #eee;
}}

tr:hover {{
    background: rgba(0,0,0,0.05);
}}

#settingsPanel {{
    position: fixed;
    top: 0;
    right: -340px;
    width: 300px;
    height: 100%;
    background: var(--card);
    box-shadow: -5px 0 20px rgba(0,0,0,0.15);
    padding: 24px;
    transition: 0.3s;
    z-index: 9999;
}}

#settingsPanel.open {{
    right: 0;
}}

.setting-item {{
    margin: 15px 0;
}}

.color-option {{
    display: block;
    padding: 10px;
    border-radius: 10px;
    margin-top: 8px;
    cursor: pointer;
    text-align: center;
    color: white;
}}

@media (max-width: 700px) {{
    body {{
        padding: 18px;
    }}

    .title {{
        font-size: 34px;
    }}
}}
</style>
</head>

<body>

<div id="settingsPanel">
    <h3>⚙ Settings</h3>

    <div class="setting-item">
        <button onclick="toggleDark()">🌙 Dark Mode</button>
    </div>

    <div class="setting-item">
        <p>Theme</p>
        <div class="color-option" style="background:#4f46e5" onclick="setColor('#4f46e5')">Blue</div>
        <div class="color-option" style="background:#16a34a" onclick="setColor('#16a34a')">Green</div>
        <div class="color-option" style="background:#dc2626" onclick="setColor('#dc2626')">Red</div>
        <div class="color-option" style="background:#f59e0b" onclick="setColor('#f59e0b')">Orange</div>
    </div>
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
    <div class="card">🏆 {top_student}<br>{top_missing}</div>
</div>

<div class="card">
    <h3>Add Record</h3>

    <form action="/add" method="post">
        <input name="level" placeholder="Level" required>
        <input name="subject" placeholder="Subject" required>
        <input name="homework" placeholder="Homework" required>
        <input name="student" placeholder="Student" required>

        <label class="checkbox-label">
            <input type="checkbox" name="priority">
            Priority
        </label>

        <br>
        <button type="submit">Add</button>
    </form>
</div>

<div class="card">
    <h3>Priority Students</h3>
    {f"<table>{priority_rows}</table>" if priority_rows else "None 🎉"}
</div>

<div class="card">
    <a href="/export">
        <button>Export CSV</button>
    </a>
</div>

<div class="card">
    <h3>Records</h3>

    <input id="search" placeholder="Search..." onkeyup="search()">

    {f'''
    <table id="table">
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
    ''' if records else "No data"}
</div>

</div>

<script>
function search() {{
    let input = document.getElementById("search").value.toLowerCase();
    let rows = document.querySelectorAll("#table tr");

    rows.forEach((row, i) => {{
        if (i === 0) return;
        row.style.display = row.innerText.toLowerCase().includes(input) ? "" : "none";
    }});
}}

function toggleSettings() {{
    document.getElementById("settingsPanel").classList.toggle("open");
}}

function toggleDark() {{
    document.body.classList.toggle("dark");
    localStorage.setItem("dark", document.body.classList.contains("dark"));
}}

function setColor(color) {{
    document.documentElement.style.setProperty('--accent', color);
    localStorage.setItem("theme", color);
}}

if (localStorage.getItem("dark") === "true") {{
    document.body.classList.add("dark");
}}

if (localStorage.getItem("theme")) {{
    document.documentElement.style.setProperty('--accent', localStorage.getItem("theme"));
}}
</script>

</body>
</html>
"""


@app.post("/add")
def add(
    level: str = Form(...),
    subject: str = Form(...),
    homework: str = Form(...),
    student: str = Form(...),
    priority: str = Form(None)
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO homework (date, level, subject, homework, student, priority)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d"),
        level.strip(),
        subject.strip(),
        homework.strip(),
        student.strip(),
        1 if priority else 0
    ))

    conn.commit()
    conn.close()

    return RedirectResponse("/", status_code=303)


@app.post("/delete/{record_id}")
def delete(record_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM homework WHERE id=?",
        (record_id,)
    )

    conn.commit()
    conn.close()

    return RedirectResponse("/", status_code=303)


@app.get("/export")
def export():
    records = load_records()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Date",
        "Level",
        "Subject",
        "Homework",
        "Student",
        "Priority"
    ])

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
        headers={
            "Content-Disposition": "attachment; filename=homework.csv"
        }
    )
