"""
MCP Bridge 缓存管理器
提供智能缓存、性能优化和数据一致性保障
"""

import asyncio
import json
import time
import hashlib
from typing import Any, Dict, Optional, Union, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from contextlib import asynccontextmanager

import aioredis
from aioredis import Redis


logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """缓存策略"""
    LRU = "lru"                    # 最近最少使用
    LFU = "lfu"                    # 最少使用频率
    TTL = "ttl"                    # 基于时间
    WRITE_THROUGH = "write_through" # 写穿透
    WRITE_BACK = "write_back"      # 写回


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    redis_url: str = "redis://localhost:6379"
    default_ttl: int = 300          # 默认TTL（秒）
    max_size: int = 1000           # 最大缓存条目数
    key_prefix: str = "mcp_bridge"  # 键前缀
    compression: bool = True        # 是否压缩
    strategy: CacheStrategy = CacheStrategy.TTL
    
    # 方法特定的TTL配置
    method_ttl: Dict[str, int] = field(default_factory=lambda: {
        "capcut_create_draft": 600,
        "capcut_upload_video": 1800,
        "capcut_get_draft": 300,
        "capcut_export_video": 3600
    })


@dataclass
class CacheMetrics:
    """缓存指标"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    total_size: int = 0
    
    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def miss_rate(self) -> float:
        """缓存未命中率"""
        return 1.0 - self.hit_rate


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    accessed_at: float
    access_count: int = 0
    ttl: Optional[int] = None
    
    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def touch(self) -> None:
        """更新访问时间和计数"""
        self.accessed_at = time.time()
        self.access_count += 1


class CacheManager:
    """缓存管理器 - 提供智能缓存和性能优化"""
    
    def __init__(self, config: CacheConfig):
        """
        初始化缓存管理器
        
        Args:
            config: 缓存配置
        """
        self.config = config
        self.redis: Optional[Redis] = None
        self.local_cache: Dict[str, CacheEntry] = {}
        self.metrics = CacheMetrics()
        self._lock = asyncio.Lock()
        
        logger.info(f"缓存管理器初始化，策略: {config.strategy.value}")
    
    async def initialize(self) -> None:
        """初始化Redis连接"""
        if self.config.enabled:
            try:
                self.redis = await aioredis.from_url(
                    self.config.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                # 测试连接
                await self.redis.ping()
                logger.info("Redis连接成功")
            except Exception as e:
                logger.error(f"Redis连接失败: {str(e)}")
                self.redis = None
    
    async def close(self) -> None:
        """关闭Redis连接"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis连接已关闭")
    
    def _generate_cache_key(self, method: str, params: Dict[str, Any]) -> str:
        """
        生成缓存键
        
        Args:
            method: MCP方法名
            params: 参数字典
            
        Returns:
            缓存键
        """
        # 创建参数的哈希值
        params_str = json.dumps(params, sort_keys=True, ensure_ascii=False)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        
        return f"{self.config.key_prefix}:{method}:{params_hash}"
    
    async def get(self, method: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            method: MCP方法名
            params: 参数字典
            
        Returns:
            缓存的值，如果不存在则返回None
        """
        if not self.config.enabled:
            return None
        
        cache_key = self._generate_cache_key(method, params)
        
        # 首先尝试本地缓存
        async with self._lock:
            local_entry = self.local_cache.get(cache_key)
            if local_entry and not local_entry.is_expired:
                local_entry.touch()
                self.metrics.hits += 1
                logger.debug(f"本地缓存命中: {cache_key}")
                return local_entry.value
        
        # 尝试Redis缓存
        if self.redis:
            try:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    value = json.loads(cached_data)
                    
                    # 更新本地缓存
                    await self._set_local_cache(cache_key, value, method)
                    
                    self.metrics.hits += 1
                    logger.debug(f"Redis缓存命中: {cache_key}")
                    return value
            except Exception as e:
                logger.error(f"Redis缓存读取失败: {str(e)}")
        
        self.metrics.misses += 1
        logger.debug(f"缓存未命中: {cache_key}")
        return None
    
    async def set(self, method: str, params: Dict[str, Any], value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值
        
        Args:
            method: MCP方法名
            params: 参数字典
            value: 要缓存的值
            ttl: 生存时间（秒），为None时使用默认值
        """
        if not self.config.enabled:
            return
        
        cache_key = self._generate_cache_key(method, params)
        
        # 确定TTL
        if ttl is None:
            ttl = self.config.method_ttl.get(method, self.config.default_ttl)
        
        # 设置Redis缓存
        if self.redis:
            try:
                cached_data = json.dumps(value, ensure_ascii=False)
                await self.redis.setex(cache_key, ttl, cached_data)
                logger.debug(f"Redis缓存设置成功: {cache_key}, TTL: {ttl}")
            except Exception as e:
                logger.error(f"Redis缓存设置失败: {str(e)}")
        
        # 设置本地缓存
        await self._set_local_cache(cache_key, value, method, ttl)
        
        self.metrics.sets += 1
    
    async def _set_local_cache(self, cache_key: str, value: Any, method: str, ttl: Optional[int] = None) -> None:
        """设置本地缓存"""
        async with self._lock:
            # 检查缓存大小限制
            if len(self.local_cache) >= self.config.max_size:
                await self._evict_local_cache()
            
            if ttl is None:
                ttl = self.config.method_ttl.get(method, self.config.default_ttl)
            
            current_time = time.time()
            self.local_cache[cache_key] = CacheEntry(
                key=cache_key,
                value=value,
                created_at=current_time,
                accessed_at=current_time,
                access_count=1,
                ttl=ttl
            )
    
    async def _evict_local_cache(self) -> None:
        """本地缓存淘汰策略"""
        if not self.local_cache:
            return
        
        if self.config.strategy == CacheStrategy.LRU:
            # 淘汰最近最少使用的条目
            oldest_key = min(self.local_cache.keys(), 
                           key=lambda k: self.local_cache[k].accessed_at)
            del self.local_cache[oldest_key]
        elif self.config.strategy == CacheStrategy.LFU:
            # 淘汰使用频率最低的条目
            least_used_key = min(self.local_cache.keys(),
                                key=lambda k: self.local_cache[k].access_count)
            del self.local_cache[least_used_key]
        elif self.config.strategy == CacheStrategy.TTL:
            # 淘汰最早过期的条目
            current_time = time.time()
            expired_keys = [
                key for key, entry in self.local_cache.items()
                if entry.is_expired
            ]
            if expired_keys:
                for key in expired_keys:
                    del self.local_cache[key]
            else:
                # 如果没有过期的，淘汰最老的
                oldest_key = min(self.local_cache.keys(),
                               key=lambda k: self.local_cache[k].created_at)
                del self.local_cache[oldest_key]
        
        self.metrics.evictions += 1
    
    async def delete(self, method: str, params: Dict[str, Any]) -> None:
        """
        删除缓存
        
        Args:
            method: MCP方法名
            params: 参数字典
        """
        if not self.config.enabled:
            return
        
        cache_key = self._generate_cache_key(method, params)
        
        # 删除Redis缓存
        if self.redis:
            try:
                await self.redis.delete(cache_key)
                logger.debug(f"Redis缓存删除成功: {cache_key}")
            except Exception as e:
                logger.error(f"Redis缓存删除失败: {str(e)}")
        
        # 删除本地缓存
        async with self._lock:
            if cache_key in self.local_cache:
                del self.local_cache[cache_key]
                self.metrics.deletes += 1
    
    async def clear(self, pattern: str = None) -> None:
        """
        清空缓存
        
        Args:
            pattern: 键模式，为None时清空所有缓存
        """
        if not self.config.enabled:
            return
        
        # 清空Redis缓存
        if self.redis:
            try:
                if pattern:
                    keys = await self.redis.keys(f"{self.config.key_prefix}:{pattern}*")
                    if keys:
                        await self.redis.delete(*keys)
                else:
                    keys = await self.redis.keys(f"{self.config.key_prefix}:*")
                    if keys:
                        await self.redis.delete(*keys)
                logger.info(f"Redis缓存清空成功，模式: {pattern or '全部'}")
            except Exception as e:
                logger.error(f"Redis缓存清空失败: {str(e)}")
        
        # 清空本地缓存
        async with self._lock:
            if pattern:
                keys_to_delete = [
                    key for key in self.local_cache.keys()
                    if pattern in key
                ]
                for key in keys_to_delete:
                    del self.local_cache[key]
            else:
                self.local_cache.clear()
            
            logger.info(f"本地缓存清空成功，模式: {pattern or '全部'}")
    
    async def cleanup_expired(self) -> int:
        """
        清理过期缓存
        
        Returns:
            清理的条目数量
        """
        if not self.config.enabled:
            return 0
        
        cleaned_count = 0
        
        # 清理本地缓存
        async with self._lock:
            expired_keys = [
                key for key, entry in self.local_cache.items()
                if entry.is_expired
            ]
            for key in expired_keys:
                del self.local_cache[key]
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"清理过期缓存: {cleaned_count} 个条目")
        
        return cleaned_count
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存信息
        
        Returns:
            缓存统计信息
        """
        async with self._lock:
            local_size = len(self.local_cache)
            local_expired = sum(1 for entry in self.local_cache.values() if entry.is_expired)
        
        redis_info = {}
        if self.redis:
            try:
                redis_info = await self.redis.info("memory")
            except Exception as e:
                logger.error(f"获取Redis信息失败: {str(e)}")
        
        return {
            "enabled": self.config.enabled,
            "strategy": self.config.strategy.value,
            "metrics": {
                "hits": self.metrics.hits,
                "misses": self.metrics.misses,
                "sets": self.metrics.sets,
                "deletes": self.metrics.deletes,
                "evictions": self.metrics.evictions,
                "hit_rate": self.metrics.hit_rate,
                "miss_rate": self.metrics.miss_rate
            },
            "local_cache": {
                "size": local_size,
                "max_size": self.config.max_size,
                "expired_entries": local_expired
            },
            "redis": redis_info,
            "config": {
                "default_ttl": self.config.default_ttl,
                "max_size": self.config.max_size,
                "compression": self.config.compression,
                "method_ttl": self.config.method_ttl
            }
        }
    
    async def warm_up(self, methods: List[str], common_params: List[Dict[str, Any]]) -> None:
        """
        缓存预热
        
        Args:
            methods: 要预热的方法列表
            common_params: 常用参数列表
        """
        if not self.config.enabled:
            return
        
        logger.info(f"开始缓存预热，方法: {methods}")
        
        # 这里可以实现预热逻辑
        # 例如：预先计算和缓存常用的请求结果
        
        logger.info("缓存预热完成")
    
    @asynccontextmanager
    async def cache_context(self, method: str, params: Dict[str, Any], ttl: Optional[int] = None):
        """
        缓存上下文管理器
        
        Args:
            method: MCP方法名
            params: 参数字典
            ttl: 生存时间
            
        Yields:
            缓存的值或None
        """
        # 尝试获取缓存
        cached_value = await self.get(method, params)
        if cached_value is not None:
            yield cached_value
            return
        
        # 缓存未命中，执行并缓存结果
        result = None
        try:
            yield None  # 表示需要执行实际操作
        except Exception as e:
            logger.error(f"缓存上下文执行失败: {str(e)}")
            raise
        
        # 注意：实际的结果需要在外部设置到缓存中
    
    async def reset_metrics(self) -> None:
        """重置缓存指标"""
        self.metrics = CacheMetrics()
        logger.info("缓存指标已重置")


# 缓存装饰器
def cached(ttl: Optional[int] = None, key_func: Optional[callable] = None):
    """
    缓存装饰器
    
    Args:
        ttl: 生存时间
        key_func: 自定义键生成函数
    """
    def decorator(func):
        async def wrapper(self, method: str, params: Dict[str, Any], *args, **kwargs):
            cache_manager = getattr(self, 'cache_manager', None)
            if not cache_manager or not cache_manager.config.enabled:
                return await func(self, method, params, *args, **kwargs)
            
            # 尝试获取缓存
            cached_result = await cache_manager.get(method, params)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = await func(self, method, params, *args, **kwargs)
            await cache_manager.set(method, params, result, ttl)
            
            return result
        
        return wrapper
    return decorator