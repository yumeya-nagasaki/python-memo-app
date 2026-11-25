import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

DB_PATH = "memos.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # カラム名で値を取り出せるようにする
    return conn


@asynccontextmanager
async def lifespan(app: FastAPI):
    # アプリ起動時にテーブルが作成されていなければ作成
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                tag TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    yield


app = FastAPI(title="学習メモアプリ", lifespan=lifespan)


# リクエストボディの型定義（バリデーション兼用）
class MemoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    tag: str = Field(default="Python", max_length=100)
    content: str = Field(..., min_length=1)


@app.get("/")
def read_index():
    return FileResponse("static/index.html")


@app.get("/api/memos")
def list_memos(q: str = ""):
    with get_connection() as conn:
        if q:
            like_q = f"%{q}%"
            rows = conn.execute(
                "SELECT * FROM memos WHERE title LIKE ? OR tag LIKE ? OR content LIKE ? ORDER BY id DESC",
                (like_q, like_q, like_q),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM memos ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]


@app.post("/api/memos", status_code=201)
def create_memo(memo: MemoCreate):
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO memos (title, tag, content) VALUES (?, ?, ?)",
            (memo.title, memo.tag, memo.content),
        )
        new_id = cursor.lastrowid
        row = conn.execute(
            "SELECT * FROM memos WHERE id = ?", (new_id,)).fetchone()
    return dict(row)


@app.delete("/api/memos/{memo_id}", status_code=204)
def delete_memo(memo_id: int):
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM memos WHERE id = ?", (memo_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Memo not found")
