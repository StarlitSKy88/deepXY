"""响应缓存模块"""

import json
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

class ModelResponseCache:
    """模型响应缓存"""
    
    def __init__(self, max_size: int = 1000, ttl_minutes: int = 60):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl_minutes = ttl_minutes
        self.access_count: Dict[str, int] = {}
        
    def _generate_cache_key(self, messages: List[Dict[str, str]], model: str) -> str:
        """生成缓存键"""
        message_str = json.dumps(messages, sort_keys=True)
        return f"{model}:{hashlib.md5(message_str.encode()).hexdigest()}"
        
    def _is_expired(self, cached_time: datetime) -> bool:
        """检查缓存是否过期"""
        return datetime.now() - cached_time > timedelta(minutes=self.ttl_minutes)
        
    async def get(self, messages: List[Dict[str, str]], model: str) -> Optional[str]:
        """获取缓存的响应"""
        key = self._generate_cache_key(messages, model)
        if key in self.cache:
            cache_data = self.cache[key]
            
            # 检查是否过期
            if self._is_expired(cache_data['timestamp']):
                del self.cache[key]
                del self.access_count[key]
                return None
                
            self.access_count[key] += 1
            return cache_data['response']
        return None
        
    async def set(self, messages: List[Dict[str, str]], model: str, response: str):
        """设置缓存"""
        key = self._generate_cache_key(messages, model)
        
        # 如果缓存已满，删除最少访问的项
        if len(self.cache) >= self.max_size:
            least_accessed = min(self.access_count.items(), key=lambda x: x[1])[0]
            del self.cache[least_accessed]
            del self.access_count[least_accessed]
            
        self.cache[key] = {
            'response': response,
            'timestamp': datetime.now()
        }
        self.access_count[key] = 1
        
    def clear_expired(self):
        """清理过期缓存"""
        current_time = datetime.now()
        expired_keys = [
            key for key, data in self.cache.items()
            if self._is_expired(data['timestamp'])
        ]
        
        for key in expired_keys:
            del self.cache[key]
            del self.access_count[key]
            
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            'total_items': len(self.cache),
            'memory_usage': sum(len(data['response'].encode()) for data in self.cache.values()),
            'hit_counts': self.access_count.copy(),
            'oldest_item': min(
                (data['timestamp'] for data in self.cache.values()),
                default=None
            ),
            'newest_item': max(
                (data['timestamp'] for data in self.cache.values()),
                default=None
            )
        } 