from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
import sqlite3
from datetime import datetime
import csv
from fastapi.responses import StreamingResponse
from io import StringIO

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
# ROUTES
# =========================

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


@app.get("/", response_class=HTMLResponse)
def home(search: str = ""):

    records = load_records()

    if search:
        records = [
            r for r in records
            if search.lower() in r["Student"].lower()
        ]

    # =========================
    # LEADERBOARD
    # =========================

    student_totals = {}

    for r in load_records():

        student = r["Student"]

        if student not in student_totals:
            student_totals[student] = 0

        student_totals[student] += 1

    sorted_students = sorted(
        student_totals.items(),
        key=lambda x: x[1],
        reverse=True
    )

    leaderboard_rows = "".join(
        f"""
        <tr>
            <td>🏆 {name}</td>
            <td>{count}</td>
        </tr>
        """
        for name, count in sorted_students[:5]
    )

    # =========================
    # STATISTICS
    # =========================

    total_records = len(load_records())

    total_priority = len([
        r for r in load_records()
        if r["Priority"] == 1
    ])

    total_students = len(set(
        r["Student"] for r in load_records()
    ))

    top_student = (
        sorted_students[0][0]
        if sorted_students else "None"
    )

    top_missing = (
        sorted_students[0][1]
        if sorted_students else 0
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

            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}

            .stat-card {{
                background: white;
                padding: 25px;
                border-radius: 18px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            }}

            .stat-number {{
                font-size: 36px;
                font-weight: bold;
                color: #2563eb;
                margin-top: 10px;
            }}

            .card h2 {{
                margin-bottom: 20px;
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
                grid-column: span 2;
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
                border: none;
                color: white;
                cursor: pointer;
            }}

            .delete-btn:hover {{
                background: #b91c1c;
            }}

            .export-btn {{
                background: #059669;
                margin-top: 15px;
            }}

            .export-btn:hover {{
                background: #047857;
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

            .empty {{
                text-align: center;
                color: #777;
                padding: 30px;
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

            .search-bar {{
                margin-bottom: 20px;
            }}

            .leaderboard-card {{
                border-left: 6px solid #f59e0b;
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

            <!-- STATISTICS -->

            <div class="stats-grid">

                <div class="stat-card">
                    📚 Total Records
                    <div class="stat-number">
                        {total_records}
                    </div>
                </div>

                <div class="stat-card">
                    👥 Unique Students
                    <div class="stat-number">
                        {total_students}
                    </div>
                </div>

                <div class="stat-card">
                    ⭐ Priority Students
                    <div class="stat-number">
                        {total_priority}
                    </div>
                </div>

                <div class="stat-card">
                    🏆 Top Missing Student
                    <div class="stat-number" style="font-size:22px;">
                        {top_student}
                    </div>

                    <div style="margin-top:10px;">
                        Missing: {top_missing}
                    </div>
                </div>

            </div>
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
    priority: str = Form(None)

):

    conn = get_connection()
    cursor = conn.cursor()

    is_priority = 1 if priority else 0

    cursor.execute("""
        SELECT *
        FROM homework
        WHERE
            level = ?
            AND subject = ?
            AND homework = ?
            AND student = ?
    """, (
        level.strip(),
        subject.strip(),
        homework.strip(),
        student.strip()
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
                priority
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d"),
            level.strip(),
            subject.strip(),
            homework.strip(),
            student.strip(),
            is_priority
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
        SELECT date, level, subject, homework, student, priority
        FROM homework
    """)

    rows = cursor.fetchall()

    conn.close()

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

    for row in rows:
        writer.writerow(row)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=homework.csv"
        }
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
