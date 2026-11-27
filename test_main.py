import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    # テストごとに一時ディレクトリ上のDBを使うよう差し替える
    test_db = tmp_path / "test_memos.db"
    monkeypatch.setattr(main, "DB_PATH", str(test_db))

    # with を使うことで main.py の lifespan（テーブル作成）が実行される
    with TestClient(main.app) as c:
        yield c


def test_create_and_list_memos(client: TestClient):
    # 1. メモを新規作成（POST）
    res = client.post(
        "/api/memos",
        json={
            "title": "pytest入門",
            "tag": "Python",
            "content": "TestClientでAPIテストが書ける",
        },
    )
    assert res.status_code == 201
    created = res.json()
    assert created["title"] == "pytest入門"
    assert "id" in created

    # 2. 一覧取得（GET）で作成したメモが返るか確認
    res = client.get("/api/memos")
    assert res.status_code == 200
    memos = res.json()
    assert len(memos) == 1
    assert memos[0]["title"] == "pytest入門"


def test_search_memos(client: TestClient):
    client.post(
        "/api/memos", json={"title": "FastAPI", "tag": "Web", "content": "ルーティング"}
    )
    client.post(
        "/api/memos", json={"title": "SQLite", "tag": "DB", "content": "テーブル作成"}
    )

    res = client.get("/api/memos", params={"q": "FastAPI"})
    assert res.status_code == 200
    memos = res.json()
    assert len(memos) == 1
    assert memos[0]["title"] == "FastAPI"


def test_delete_memo(client: TestClient):
    created = client.post(
        "/api/memos",
        json={"title": "削除テスト", "tag": "Test", "content": "すぐ消すメモ"},
    ).json()

    # 削除成功（204 No Content）
    res = client.delete(f"/api/memos/{created['id']}")
    assert res.status_code == 204

    # 存在しないIDを消そうとすると 404
    res = client.delete(f"/api/memos/{created['id']}")
    assert res.status_code == 404


def test_create_memo_validation_error(client: TestClient):
    # タイトルが空文字の場合は Pydantic により 422 エラーになる
    res = client.post(
        "/api/memos",
        json={"title": "", "tag": "Python", "content": "本文あり"},
    )
    assert res.status_code == 422
