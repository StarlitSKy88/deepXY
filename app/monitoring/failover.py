"""模型回退处理模块"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta

class ModelFailoverHandler:
    """模型回退处理"""
    
    def __init__(self, models: List[str], max_retries: int = 3, cooldown_minutes: int = 5):
        self.models = models
        self.max_retries = max_retries
        self.cooldown_minutes = cooldown_minutes
        self.current_model_index = 0
        self.retry_count = 0
        self.model_cooldowns: Dict[str, datetime] = {}
        
    async def get_next_model(self, error: Optional[str] = None) -> Optional[str]:
        """获取下一个可用模型"""
        if self.retry_count >= self.max_retries:
            return None
            
        self.retry_count += 1
        
        # 检查所有模型,找到一个不在冷却期的模型
        original_index = self.current_model_index
        while True:
            self.current_model_index = (self.current_model_index + 1) % len(self.models)
            candidate_model = self.models[self.current_model_index]
            
            # 检查模型是否在冷却期
            if candidate_model in self.model_cooldowns:
                cooldown_end = self.model_cooldowns[candidate_model]
                if datetime.now() < cooldown_end:
                    # 如果已经检查了所有模型,返回None
                    if self.current_model_index == original_index:
                        return None
                    continue
                    
            # 找到一个可用的模型
            if error:
                # 将失败的模型放入冷却期
                self.model_cooldowns[candidate_model] = datetime.now() + timedelta(minutes=self.cooldown_minutes)
            return candidate_model
        
    def reset(self):
        """重置回退状态"""
        self.current_model_index = 0
        self.retry_count = 0
        
    def get_cooldown_status(self) -> Dict[str, str]:
        """获取所有模型的冷却状态"""
        now = datetime.now()
        return {
            model: (self.model_cooldowns[model] - now).total_seconds()
            for model in self.model_cooldowns
            if now < self.model_cooldowns[model]
        } 