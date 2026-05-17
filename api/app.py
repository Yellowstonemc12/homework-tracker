from fastapi import FastAPI, Form
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    Response,
    FileResponse
)

import sqlite3
from datetime import datetime
import csv

app = FastAPI()

DB_PATH = "/tmp/homework.db"


# =========================
# DATABASE
# =========================

def get_connection():
    return sqlite3.connect(DB_PATH)


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
            priority INTEGER DEFAULT 0,
            submitted INTEGER DEFAULT 0
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
        SELECT
            id,
            date,
            level,
            subject,
            homework,
            student,
            priority,
            submitted
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
            "Submitted": r[7],
        }
        for r in rows
    ]


# =========================
# STUDENT MISSING COUNT
# =========================

def get_student_count(student_name):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM homework
        WHERE student = ?
    """, (student_name,))

    count = cursor.fetchone()[0]

    conn.close()

    return count


# =========================
# LEADERBOARD
# =========================

def get_top_students():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT student, COUNT(*)
        FROM homework
        GROUP BY student
        ORDER BY COUNT(*) DESC
        LIMIT 5
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


# =========================
# ROUTES
# =========================

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


# =========================
# HOME PAGE
# =========================

@app.get("/", response_class=HTMLResponse)
def home():

    records = load_records()

    leaderboard = get_top_students()

    total_priority = len(
        [r for r in records if r["Priority"] == 1]
    )

    total_students = len(
        set(r["Student"] for r in records)
    )

    # =========================
    # PRIORITY TABLE
    # =========================

    priority_rows = "".join(
        f"""
        <tr>
            <td>{r['Student']}</td>
            <td>{r['Homework']}</td>
            <td>{r['Subject']}</td>

            <td>
                <span class='priority-badge'>
                    ⭐ PRIORITY
                </span>
            </td>
        </tr>
        """
        for r in records
        if r["Priority"] == 1
    )

    # =========================
    # LEADERBOARD
    # =========================

    leaderboard_rows = "".join(
        f"""
        <tr>
            <td>{student}</td>
            <td>{count}</td>
        </tr>
        """
        for student, count in leaderboard
    )

    # =========================
    # MAIN TABLE
    # =========================

    rows = "".join(
        f"""
        <tr>

            <td>{r['Date']}</td>

            <td>{r['Level']}</td>

            <td>{r['Subject']}</td>

            <td>{r['Homework']}</td>

            <td>

                {r['Student']}

                {
                    "<span class='priority-badge'>⭐</span>"
                    if r['Priority'] == 1 else ""
                }

                <span class='counter-badge'>
                    Missing: {get_student_count(r['Student'])}
                </span>

            </td>

            <td>

                {
                    "<span class='submitted-badge'>✅ Submitted</span>"
                    if r['Submitted'] == 1
                    else "<span class='missing-badge'>❌ Missing</span>"
                }

            </td>

            <td>

                <form action="/delete/{r['ID']}" method="post">

                    <button class="delete-btn" type="submit">
                        🗑 Delete
                    </button>

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

            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: Arial, sans-serif;
            }}

            body {{
                background: #f4f7fb;
                color: #222;
                padding: 40px;
                transition: 0.3s;
            }}

            .dark-mode {{
                background: #111827;
                color: white;
            }}

            .dark-mode .card {{
                background: #1f2937;
                color: white;
            }}

            .container {{
                max-width: 1200px;
                margin: auto;
            }}

            .title {{
                font-size: 42px;
                font-weight: bold;
                margin-bottom: 10px;
            }}

            .subtitle {{
                color: #666;
                margin-bottom: 35px;
            }}

            .card {{
                background: white;
                padding: 25px;
                border-radius: 18px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                margin-bottom: 30px;
            }}

            .card h2 {{
                margin-bottom: 20px;
            }}

            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin-bottom: 30px;
            }}

            .add-form {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
            }}

            input {{
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 10px;
                font-size: 15px;
            }}

            button {{
                padding: 14px;
                border: none;
                border-radius: 12px;
                background: #2563eb;
                color: white;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                transition: 0.2s;
            }}

            button:hover {{
                background: #1d4ed8;
            }}

            .delete-btn {{
                background: #dc2626;
                padding: 8px 12px;
                border-radius: 8px;
                font-size: 14px;
            }}

            .delete-btn:hover {{
                background: #b91c1c;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                overflow: hidden;
                border-radius: 12px;
            }}

            th {{
                background: #2563eb;
                color: white;
                padding: 14px;
                text-align: left;
            }}

            td {{
                padding: 14px;
                border-bottom: 1px solid #eee;
            }}

            tr:hover {{
                background: #f9fbff;
            }}

            .badge {{
                display: inline-block;
                background: #2563eb;
                color: white;
                padding: 6px 12px;
                border-radius: 999px;
                font-size: 14px;
                margin-bottom: 15px;
            }}

            .priority-label {{
                display: flex;
                align-items: center;
                gap: 10px;
                font-weight: bold;
                color: #d97706;
            }}

            .priority-badge {{
                display: inline-block;
                background: #facc15;
                color: #222;
                padding: 4px 10px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: bold;
                margin-left: 8px;
            }}

            .counter-badge {{
                display: inline-block;
                background: #ef4444;
                color: white;
                padding: 4px 10px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: bold;
                margin-left: 8px;
            }}

            .submitted-badge {{
                background: #22c55e;
                color: white;
                padding: 5px 10px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: bold;
            }}

            .missing-badge {{
                background: #ef4444;
                color: white;
                padding: 5px 10px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: bold;
            }}

            .top-buttons {{
                display: flex;
                gap: 15px;
                margin-bottom: 20px;
            }}

            @media (max-width: 700px) {{

                body {{
                    padding: 20px;
                }}

                .add-form {{
                    grid-template-columns: 1fr;
                }}

                .stats-grid {{
                    grid-template-columns: 1fr;
                }}

                .title {{
                    font-size: 32px;
                }}

                table {{
                    font-size: 14px;
                    display: block;
                    overflow-x: auto;
                }}
            }}

        </style>

    </head>

    <body>

        <div class="container">

            <div class="title">
                📘 Homework Tracker
            </div>

            <div class="subtitle">
                Manage student homework submissions easily
            </div>

            <div class="top-buttons">

                <button onclick="toggleDarkMode()">
                    🌙 Dark Mode
                </button>

                <a href="/export">
                    <button>
                        📥 Export CSV
                    </button>
                </a>

            </div>

            <!-- SEARCH -->

            <div class="card">

                <input
                    type="text"
                    id="searchInput"
                    placeholder="🔍 Search student..."
                    onkeyup="searchTable()"
                >

            </div>

            <!-- STATS -->

            <div class="stats-grid">

                <div class="card">
                    <h3>Total Records</h3>
                    <p>{len(records)}</p>
                </div>

                <div class="card">
                    <h3>Priority Students</h3>
                    <p>{total_priority}</p>
                </div>

                <div class="card">
                    <h3>Total Students</h3>
                    <p>{total_students}</p>
                </div>

            </div>

            <!-- LEADERBOARD -->

            <div class="card">

                <h2>🏆 Top Missing Homework Students</h2>

                <table>

                    <tr>
                        <th>Student</th>
                        <th>Missing Count</th>
                    </tr>

                    {leaderboard_rows}

                </table>

            </div>

            <!-- PRIORITY -->

            <div class="card">

                <h2>⭐ Priority Students</h2>

                {
                    f'''
                    <table>

                        <tr>
                            <th>Student</th>
                            <th>Homework</th>
                            <th>Subject</th>
                            <th>Status</th>
                        </tr>

                        {priority_rows}

                    </table>
                    '''
                    if priority_rows
                    else
                    '<div>No priority students 🎉</div>'
                }

            </div>

            <!-- ADD RECORD -->

            <div class="card">

                <div class="badge">
                    Total Records: {len(records)}
                </div>

                <h2>Add Record</h2>

                <form class="add-form" action="/add" method="post">

                    <input
                        type="text"
                        name="level"
                        placeholder="Primary Level"
                        required
                    >

                    <input
                        type="text"
                        name="subject"
                        placeholder="Subject"
                        required
                    >

                    <input
                        type="text"
                        name="homework"
                        placeholder="Homework Name"
                        required
                    >

                    <input
                        type="text"
                        name="student"
                        placeholder="Student Name"
                        required
                    >

                    <label class="priority-label">

                        <input type="checkbox" name="priority">

                        ⭐ Priority Student

                    </label>

                    <label class="priority-label">

                        <input type="checkbox" name="submitted">

                        ✅ Submitted

                    </label>

                    <button type="submit">
                        Add Record
                    </button>

                </form>

            </div>

            <!-- RECORDS -->

            <div class="card">

                <h2>📋 Records</h2>

                <table id="recordsTable">

                    <tr>
                        <th>Date</th>
                        <th>Level</th>
                        <th>Subject</th>
                        <th>Homework</th>
                        <th>Student</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>

                    {rows}

                </table>

            </div>

        </div>

        <script>

            function toggleDarkMode() {{

                document.body.classList.toggle("dark-mode");

            }}

            function searchTable() {{

                let input =
                    document.getElementById("searchInput");

                let filter =
                    input.value.toLowerCase();

                let table =
                    document.getElementById("recordsTable");

                let tr =
                    table.getElementsByTagName("tr");

                for (let i = 1; i < tr.length; i++) {{

                    let td =
                        tr[i].getElementsByTagName("td")[4];

                    if (td) {{

                        let txtValue =
                            td.textContent || td.innerText;

                        tr[i].style.display =
                            txtValue.toLowerCase().includes(filter)
                            ? ""
                            : "none";
                    }}
                }}
            }}

        </script>

    </body>

    </html>
    """


# =========================
# ADD RECORD
# =========================

@app.post("/add")
def add(

    level: str = Form(...),
    subject: str = Form(...),
    homework: str = Form(...),
    student: str = Form(...),
    priority: str = Form(None),
    submitted: str = Form(None)

):

    conn = get_connection()
    cursor = conn.cursor()

    is_priority = 1 if priority else 0
    is_submitted = 1 if submitted else 0

    # SMART DUPLICATE DETECTION

    cursor.execute("""
        SELECT *
        FROM homework
        WHERE
            level = ?
            AND subject = ?
            AND homework = ?
            AND student = ?
            AND date = ?
    """, (
        level.strip(),
        subject.strip(),
        homework.strip(),
        student.strip(),
        datetime.now().strftime("%Y-%m-%d")
    ))

    existing = cursor.fetchone()

    if not existing:

        cursor.execute("""
            INSERT INTO homework (
                date,
                level,
                subject,
                homework,
                student,
                priority,
                submitted
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d"),
            level.strip(),
            subject.strip(),
            homework.strip(),
            student.strip(),
            is_priority,
            is_submitted
        ))

        conn.commit()

    conn.close()

    return RedirectResponse("/", status_code=303)


# =========================
# EXPORT CSV
# =========================

@app.get("/export")
def export_csv():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM homework
    """)

    rows = cursor.fetchall()

    conn.close()

    file_path = "/tmp/homework_export.csv"

    with open(file_path, "w", newline="") as csvfile:

        writer = csv.writer(csvfile)

        writer.writerow([
            "ID",
            "Date",
            "Level",
            "Subject",
            "Homework",
            "Student",
            "Priority",
            "Submitted"
        ])

        writer.writerows(rows)

    return FileResponse(
        file_path,
        media_type="text/csv",
        filename="homework_export.csv"
    )


# =========================
# DELETE RECORD
# =========================

@app.post("/delete/{record_id}")
def delete_record(record_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM homework WHERE id = ?",
        (record_id,)
    )

    conn.commit()
    conn.close()

    return RedirectResponse("/", status_code=303)
