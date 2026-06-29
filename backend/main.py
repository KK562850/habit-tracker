from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3
from datetime import date, timedelta
from contextlib import contextmanager
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "habits.db")

app = FastAPI(title="Habit Tracker API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (date('now')),
                sort_order INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
                date TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 1,
                UNIQUE(habit_id, date)
            );
        """)


def compute_streak(conn, habit_id: int) -> int:
    rows = conn.execute(
        "SELECT date FROM completions WHERE habit_id=? AND completed=1 ORDER BY date DESC",
        (habit_id,)
    ).fetchall()
    if not rows:
        return 0
    dates = {r["date"] for r in rows}
    today = date.today()
    # streak must include today or yesterday to be active
    if today.isoformat() not in dates and (today - timedelta(days=1)).isoformat() not in dates:
        return 0
    cursor = today if today.isoformat() in dates else today - timedelta(days=1)
    streak = 0
    while cursor.isoformat() in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


class HabitCreate(BaseModel):
    name: str


class ReorderRequest(BaseModel):
    ordered_ids: list[int]


STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.on_event("startup")
def startup():
    init_db()


@app.get("/habits")
def list_habits():
    today = date.today().isoformat()
    with get_db() as conn:
        habits = conn.execute(
            "SELECT id, name, created_at FROM habits ORDER BY sort_order, id"
        ).fetchall()
        result = []
        for h in habits:
            completed_row = conn.execute(
                "SELECT completed FROM completions WHERE habit_id=? AND date=?",
                (h["id"], today)
            ).fetchone()
            completed = bool(completed_row and completed_row["completed"])
            streak = compute_streak(conn, h["id"])
            result.append({
                "id": h["id"],
                "name": h["name"],
                "created_at": h["created_at"],
                "completed_today": completed,
                "streak": streak,
            })
    return result


@app.post("/habits", status_code=201)
def create_habit(body: HabitCreate):
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "Name is required")
    with get_db() as conn:
        max_order = conn.execute("SELECT COALESCE(MAX(sort_order),0) FROM habits").fetchone()[0]
        cur = conn.execute(
            "INSERT INTO habits (name, created_at, sort_order) VALUES (?, date('now'), ?)",
            (name, max_order + 1)
        )
        habit_id = cur.lastrowid
        return {"id": habit_id, "name": name, "completed_today": False, "streak": 0}


@app.post("/habits/{habit_id}/toggle")
def toggle_completion(habit_id: int):
    today = date.today().isoformat()
    with get_db() as conn:
        habit = conn.execute("SELECT id FROM habits WHERE id=?", (habit_id,)).fetchone()
        if not habit:
            raise HTTPException(404, "Habit not found")
        existing = conn.execute(
            "SELECT completed FROM completions WHERE habit_id=? AND date=?",
            (habit_id, today)
        ).fetchone()
        if existing is None:
            conn.execute(
                "INSERT INTO completions (habit_id, date, completed) VALUES (?, ?, 1)",
                (habit_id, today)
            )
            new_state = True
        else:
            new_state = not bool(existing["completed"])
            conn.execute(
                "UPDATE completions SET completed=? WHERE habit_id=? AND date=?",
                (int(new_state), habit_id, today)
            )
        streak = compute_streak(conn, habit_id)
        return {"habit_id": habit_id, "completed_today": new_state, "streak": streak}


@app.delete("/habits/{habit_id}", status_code=204)
def delete_habit(habit_id: int):
    with get_db() as conn:
        result = conn.execute("DELETE FROM habits WHERE id=?", (habit_id,))
        if result.rowcount == 0:
            raise HTTPException(404, "Habit not found")
    return None


@app.patch("/habits/{habit_id}")
def update_habit(habit_id: int, body: HabitCreate):
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "Name is required")
    with get_db() as conn:
        result = conn.execute("UPDATE habits SET name=? WHERE id=?", (name, habit_id))
        if result.rowcount == 0:
            raise HTTPException(404, "Habit not found")
        return {"id": habit_id, "name": name}


@app.post("/habits/reorder")
def reorder_habits(body: ReorderRequest):
    with get_db() as conn:
        for order, habit_id in enumerate(body.ordered_ids):
            conn.execute("UPDATE habits SET sort_order=? WHERE id=?", (order, habit_id))
    return {"ok": True}
