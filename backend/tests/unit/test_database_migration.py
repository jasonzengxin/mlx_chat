import aiosqlite
import pytest

from backend import main


@pytest.mark.asyncio
async def test_get_database_migrates_messages_duration_ms(tmp_path):
    db_path = tmp_path / "legacy.db"

    conn = await aiosqlite.connect(db_path)
    await conn.executescript("""
        CREATE TABLE messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    await conn.commit()
    await conn.close()

    original_db_path = main.DB_PATH
    main.DB_PATH = str(db_path)

    try:
        db = await main.get_database()
        columns = await db.fetchall("PRAGMA table_info(messages)")
        assert any(column["name"] == "duration_ms" for column in columns)
        await db.close()
    finally:
        main.DB_PATH = original_db_path
