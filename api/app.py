from fastapi import FastAPI, Form
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

# ================= DATA =================
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
    cursor.execute("SELECT student, COUNT(*) FROM homework GROUP BY student")
    data = dict(cursor.fetchall())
    conn.close()
    return data

def get_top_student(counts):
    if not counts:
        return ("None", 0)
    top = max(counts, key=counts.get)
    return (top, counts[top])

# ================= ROUTES =================
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
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Homework Tracker</title>

<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600&display=swap" rel="stylesheet">

<style>
:root {{
    --bg: #fff0f6;
    --card: #ffffff;
    --text: #2d2d2d;
    --accent: #ff6fa5;
}}

.dark {{
    --bg: #0f172a;
    --card: #1e293b;
    --text: #e2e8f0;
}}

body {{
    font-family: 'Fredoka', sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 30px;
}}

.container {{
    max-width: 1100px;
    margin: auto;
}}

.title {{
    font-size: 52px;
    font-weight: 600;
    color: var(--accent);
    display: flex;
    align-items: center;
    gap: 10px;
}}

.card {{
    background: var(--card);
    padding: 22px;
    border-radius: 20px;
    margin-bottom: 20px;
    box-shadow: 0 10px 25px rgba(255,105,180,0.15);
}}

.grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px,1fr));
    gap: 20px;
}}

.big {{
    font-size: 32px;
    color: var(--accent);
}}

input {{
    padding: 12px;
    border-radius: 12px;
    border: 2px solid #ffd6e7;
    margin: 5px;
}}

input:focus {{
    border-color: var(--accent);
    outline: none;
}}

button {{
    padding: 10px 16px;
    border-radius: 14px;
    border: none;
    background: linear-gradient(135deg, #ff6fa5, #ff9ecb);
    color: white;
    cursor: pointer;
}}

.delete {{
    background: #ff4d6d;
}}

.badge {{
    background: #ff6b6b;
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
}}

th {{
    background: #ff6fa5;
    color: white;
    padding: 10px;
    border-radius: 6px;
}}

td {{
    padding: 10px;
    border-bottom: 1px solid #eee;
}}

tr:hover {{
    background: rgba(0,0,0,0.05);
}}

.toggle {{
    margin-left: auto;
    cursor: pointer;
}}
</style>
</head>

<body>
<div class="container">

<div class="title">
<img src="https://cdn-icons-png.flaticon.com/512/2436/2436636.png" width="45">
Homework Tracker
<span class="toggle" onclick="toggleDark()">🌙</span>
</div>

<!-- STATS -->
<div class="grid">
<div class="card">📚<div class="big">{total}</div></div>
<div class="card">👩‍🎓<div class="big">{unique}</div></div>
<div class="card">⭐<div class="big">{priority_count}</div></div>
<div class="card">🏆 {top_student}<br>{top_missing}</div>
</div>

<!-- ADD -->
<div class="card">
<h3>Add Record</h3>
<form action="/add" method="post">
<input name="level" placeholder="Level" required>
<input name="subject" placeholder="Subject" required>
<input name="homework" placeholder="Homework" required>
<input name="student" placeholder="Student" required>
<label><input type="checkbox" name="priority"> Priority</label>
<button>Add ✨</button>
</form>
</div>

<!-- PRIORITY -->
<div class="card">
<h3>⭐ Priority Students</h3>
{f"<table>{priority_rows}</table>" if priority_rows else "None 🎉"}
</div>

<!-- EXPORT -->
<div class="card">
<a href="/export"><button>📥 Export CSV</button></a>
</div>

<!-- RECORDS -->
<div class="card">
<h3>Records</h3>

<input id="search" placeholder="🔍 Search..." onkeyup="search()">

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
''' if records else "No data 💤"}

</div>

</div>

<script>
function search() {{
    let input = document.getElementById("search").value.toLowerCase();
    let rows = document.querySelectorAll("#table tr");
    rows.forEach((row,i)=>{{
        if(i===0)return;
        row.style.display = row.innerText.toLowerCase().includes(input) ? "" : "none";
    }});
}}

function toggleDark() {{
    document.body.classList.toggle("dark");
    localStorage.setItem("dark", document.body.classList.contains("dark"));
}}

if(localStorage.getItem("dark")==="true") {{
    document.body.classList.add("dark");
}}
</script>

</body>
</html>
"""

# ================= ADD =================
@app.post("/add")
def add(level: str = Form(...), subject: str = Form(...),
        homework: str = Form(...), student: str = Form(...),
        priority: str = Form(None)):

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

# ================= DELETE =================
@app.post("/delete/{record_id}")
def delete(record_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM homework WHERE id=?", (record_id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/", status_code=303)

# ================= EXPORT =================
@app.get("/export")
def export():
    records = load_records()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date","Level","Subject","Homework","Student","Priority"])
    for r in records:
        writer.writerow([r["Date"], r["Level"], r["Subject"], r["Homework"], r["Student"], r["Priority"]])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=homework.csv"})
