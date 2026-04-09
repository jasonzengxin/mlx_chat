"""
数据库辅助类

封装 aiosqlite 操作，提供简化的 API
"""

import aiosqlite


class Database:
    """数据库辅助类"""

    def __init__(self, connection: aiosqlite.Connection):
        self._connection = connection

    @property
    def connection(self) -> aiosqlite.Connection:
        return self._connection

    async def execute(self, query: str, params: tuple = ()) -> aiosqlite.Cursor:
        """执行 SQL"""
        return await self._connection.execute(query, params)

    async def executemany(self, query: str, params_list: list) -> aiosqlite.Cursor:
        """批量执行 SQL"""
        return await self._connection.executemany(query, params_list)

    async def executescript(self, script: str) -> None:
        """执行脚本"""
        await self._connection.executescript(script)

    async def commit(self) -> None:
        """提交事务"""
        await self._connection.commit()

    async def rollback(self) -> None:
        """回滚事务"""
        await self._connection.rollback()

    async def fetchone(self, query: str, params: tuple = ()) -> dict | None:
        """查询单行"""
        cursor = await self._connection.execute(query, params)
        row = await cursor.fetchone()
        if row is None:
            return None
        # 转换为字典
        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, row))

    async def fetchall(self, query: str, params: tuple = ()) -> list[dict]:
        """查询多行"""
        cursor = await self._connection.execute(query, params)
        rows = await cursor.fetchall()
        if not rows:
            return []
        # 转换为字典列表
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    async def fetchval(self, query: str, params: tuple = ()) -> any:
        """查询单个值"""
        cursor = await self._connection.execute(query, params)
        row = await cursor.fetchone()
        if row is None:
            return None
        return row[0]

    async def close(self) -> None:
        """关闭连接"""
        await self._connection.close()