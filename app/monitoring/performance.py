"""性能监控模块"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ModelMetrics:
    """模型性能指标"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_tokens: int = 0
    total_time: float = 0
    errors: list = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)

class ModelPerformanceMonitor:
    """模型性能监控"""
    
    def __init__(self):
        self.metrics: Dict[str, ModelMetrics] = {}
        
    async def record_performance(
        self, 
        model: str, 
        start_time: float,
        end_time: float,
        token_count: int,
        success: bool,
        error: Optional[str] = None
    ):
        """记录模型性能指标"""
        if model not in self.metrics:
            self.metrics[model] = ModelMetrics()
            
        metrics = self.metrics[model]
        metrics.total_calls += 1
        if success:
            metrics.successful_calls += 1
            metrics.total_tokens += token_count
            metrics.total_time += (end_time - start_time)
        else:
            metrics.failed_calls += 1
            if error:
                metrics.errors.append({
                    'time': datetime.now(),
                    'error': error
                })
        metrics.last_updated = datetime.now()
                
    def get_model_stats(self, model: str) -> Dict[str, Any]:
        """获取模型统计信息"""
        if model not in self.metrics:
            return {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_tokens': 0,
                'total_time': 0,
                'success_rate': 0,
                'average_response_time': 0,
                'average_tokens': 0,
                'error_rate': 0,
                'recent_errors': [],
                'last_updated': None
            }
            
        metrics = self.metrics[model]
        successful_calls = metrics.successful_calls
        
        if successful_calls > 0:
            avg_time = metrics.total_time / successful_calls
            avg_tokens = metrics.total_tokens / successful_calls
        else:
            avg_time = 0
            avg_tokens = 0
            
        return {
            'total_calls': metrics.total_calls,
            'successful_calls': successful_calls,
            'failed_calls': metrics.failed_calls,
            'total_tokens': metrics.total_tokens,
            'total_time': metrics.total_time,
            'success_rate': successful_calls / metrics.total_calls if metrics.total_calls > 0 else 0,
            'average_response_time': avg_time,
            'average_tokens': avg_tokens,
            'error_rate': metrics.failed_calls / metrics.total_calls if metrics.total_calls > 0 else 0,
            'recent_errors': [e for e in metrics.errors[-5:]],  # 最近5个错误
            'last_updated': metrics.last_updated.isoformat() if metrics.last_updated else None
        }
        
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有模型的统计信息"""
        return {
            model: self.get_model_stats(model)
            for model in self.metrics
        } 