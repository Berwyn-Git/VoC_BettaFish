"""
ExpertEngine状态管理
定义专家批注过程中的状态数据结构
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import json
from datetime import datetime


@dataclass
class ExpertState:
    """专家批注状态管理"""
    # 基本信息
    query: str = ""                      # 原始查询
    status: str = "pending"              # 状态: pending, processing, completed, failed
    
    # 输入数据
    original_content: str = ""           # 原始报告内容
    business_rules: str = ""             # 业务逻辑要求
    
    # 处理结果
    reviewed_content: str = ""           # 批注后的报告内容
    
    # 元数据
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def mark_processing(self):
        """标记为处理中"""
        self.status = "processing"
    
    def mark_completed(self):
        """标记为完成"""
        self.status = "completed"
    
    def mark_failed(self, error_message: str = ""):
        """标记为失败"""
        self.status = "failed"
        self.error_message = error_message
    
    def is_completed(self) -> bool:
        """检查是否完成"""
        return self.status == "completed" and bool(self.reviewed_content)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "query": self.query,
            "status": self.status,
            "has_reviewed_content": bool(self.reviewed_content),
            "reviewed_content_length": len(self.reviewed_content) if self.reviewed_content else 0,
            "timestamp": self.timestamp
        }
    
    def save_to_file(self, file_path: str):
        """保存状态到文件"""
        try:
            state_data = self.to_dict()
            # 不保存完整的批注内容到状态文件（太大）
            state_data.pop("reviewed_content", None)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存状态文件失败: {str(e)}")
    
    @classmethod
    def load_from_file(cls, file_path: str) -> Optional["ExpertState"]:
        """从文件加载状态"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 创建ExpertState对象
            state = cls(
                query=data.get("query", ""),
                status=data.get("status", "pending")
            )
            
            return state
            
        except Exception as e:
            print(f"加载状态文件失败: {str(e)}")
            return None

