"""Redis 客户端（用于缓存/任务队列）"""

import redis.asyncio as aioredis
from app.core.config import settings

redis_client: aioredis.Redis | None = None


async def init_redis():
    """初始化 Redis 连接"""
    global redis_client
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )


async def close_redis():
    """关闭 Redis 连接"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


def get_redis() -> aioredis.Redis:
    """获取 Redis 客户端实例"""
    if redis_client is None:
        raise RuntimeError("Redis 尚未初始化")
    return redis_client
