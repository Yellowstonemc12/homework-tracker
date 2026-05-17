from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
import sqlite3
from datetime import datetime

app = FastAPI()
DB_PATH = "/tmp/homework.db"

# =========================
# DATABASE
# =========================
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

# =========================
# LOAD RECORDS
# =========================
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

# =========================
# COUNTS (FAST)
# =========================
def get_all_student_counts():
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

# =========================
# ROUTES
# =========================
@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

@app.get("/", response_class=HTMLResponse)
def home():
    records = load_records()
    counts = get_all_student_counts()

    total = len(records)
    unique = len(counts)
    priority_count = len([r for r in records if r["Priority"] == 1])
    top_student, top_missing = get_top_student(counts)

    # PRIORITY TABLE
    priority_rows = "".join(
        f"""
        <tr>
            <td>{r['Student']}</td>
            <td>{r['Homework']}</td>
            <td>{r['Subject']}</td>
            <td><span class='priority'>⭐ PRIORITY</span></td>
        </tr>
        """
        for r in records if r["Priority"] == 1
    )

    # RECORDS
    rows = "".join(
        f"""
        <tr>
            <td>{r['Date']}</td>
            <td>{r['Level']}</td>
            <td>{r['Subject']}</td>
            <td>{r['Homework']}</td>
            <td>
                {r['Student']}
                {"<span class='priority'>⭐</span>" if r['Priority'] else ""}
                <span class='badge'>
                    Missing: {counts.get(r['Student'], 0)}
                </span>
            </td>
            <td>
                <form action="/delete/{r['ID']}" method="post">
                    <button class="delete">🗑</button>
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
        <title>Homework Tracker</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
        body {{
            font-family: Arial;
            background: #f4f7fb;
            padding: 40px;
        }}

        .container {{
            max-width: 1100px;
            margin: auto;
        }}

        .title {{
            font-size: 48px;
            font-weight: bold;
        }}

        .subtitle {{
            color: #666;
            margin-bottom: 30px;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px,1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .card {{
            background: white;
            padding: 20px;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }}

        .big {{
            font-size: 32px;
            font-weight: bold;
            color: #2563eb;
        }}

        input {{
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #ddd;
        }}

        button {{
            padding: 10px;
            background: #2563eb;
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
        }}

        .delete {{
            background: red;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}

        th {{
            background: #2563eb;
            color: white;
            padding: 10px;
        }}

        td {{
            padding: 10px;
            border-bottom: 1px solid #eee;
        }}

        .priority {{
            background: gold;
            padding: 4px 8px;
            border-radius: 10px;
            margin-left: 5px;
        }}

        .badge {{
            background: red;
            color: white;
            padding: 4px 8px;
            border-radius: 10px;
            margin-left: 5px;
        }}

        .search {{
            width: 100%;
            margin-bottom: 10px;
        }}

        </style>
    </head>

    <body>
    <div class="container">

        <div class="title">📘 Homework Tracker</div>
        <div class="subtitle">Clean + cute version restored ✨</div>

        <!-- STATS -->
        <div class="grid">
            <div class="card">📚<br><div class="big">{total}</div></div>
            <div class="card">👥<br><div class="big">{unique}</div></div>
            <div class="card">⭐<br><div class="big">{priority_count}</div></div>
            <div class="card">🏆<br>{top_student}<br>{top_missing}</div>
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
                <button>Add</button>
            </form>
        </div>

        <!-- PRIORITY -->
        <div class="card">
            <h3>⭐ Priority</h3>
            {f"<table>{priority_rows}</table>" if priority_rows else "None 🎉"}
        </div>

        <!-- RECORDS -->
        <div class="card">
            <h3>Records</h3>
            <input class="search" id="search" placeholder="🔍 Search..." onkeyup="search()">
            {f"<table id='table'>{rows}</table>" if records else "No data"}
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
    </script>

    </body>
    </html>
    """

# =========================
# ADD
# =========================
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

# =========================
# DELETE
# =========================
@app.post("/delete/{record_id}")
def delete_record(record_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM homework WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/", status_code=303)
