import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI
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
