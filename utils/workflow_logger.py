"""
工作流日志记录模块
记录工作流中间的重要信息输入、加工、分析，以及通讯用时、分析用时、信息延迟等
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from loguru import logger


@dataclass
class WorkflowLogEntry:
    """工作流日志条目"""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    module_name: str = ""                    # 模块名称
    step_name: str = ""                      # 步骤名称
    operation_type: str = ""                 # 操作类型: input, process, output, communication
    input_info: Dict[str, Any] = field(default_factory=dict)  # 输入信息
    output_info: Dict[str, Any] = field(default_factory=dict)  # 输出信息
    communication_time: float = 0.0          # 通讯用时（秒）
    analysis_time: float = 0.0               # 分析用时（秒）
    information_delay: float = 0.0          # 信息延迟（秒）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据


class WorkflowLogger:
    """工作流日志记录器"""
    
    def __init__(self, log_file: Optional[str] = None):
        """
        初始化工作流日志记录器
        
        Args:
            log_file: 日志文件路径，如果为None则使用默认路径
        """
        if log_file is None:
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"workflow_{timestamp}.json")
        
        self.log_file = log_file
        self.entries: List[WorkflowLogEntry] = []
        self.current_query: str = ""
        
        logger.info(f"工作流日志记录器已初始化，日志文件: {self.log_file}")
    
    def set_query(self, query: str):
        """设置当前查询"""
        self.current_query = query
    
    def log_input(self, module_name: str, step_name: str, input_info: Dict[str, Any], 
                  metadata: Optional[Dict[str, Any]] = None):
        """
        记录输入信息
        
        Args:
            module_name: 模块名称
            step_name: 步骤名称
            input_info: 输入信息
            metadata: 元数据
        """
        entry = WorkflowLogEntry(
            module_name=module_name,
            step_name=step_name,
            operation_type="input",
            input_info=input_info,
            metadata=metadata or {}
        )
        self.entries.append(entry)
        logger.debug(f"[工作流日志] {module_name}.{step_name} - 输入信息已记录")
    
    def log_process(self, module_name: str, step_name: str, 
                   analysis_time: float, input_info: Optional[Dict[str, Any]] = None,
                   output_info: Optional[Dict[str, Any]] = None,
                   metadata: Optional[Dict[str, Any]] = None):
        """
        记录处理过程
        
        Args:
            module_name: 模块名称
            step_name: 步骤名称
            analysis_time: 分析用时（秒）
            input_info: 输入信息
            output_info: 输出信息
            metadata: 元数据
        """
        entry = WorkflowLogEntry(
            module_name=module_name,
            step_name=step_name,
            operation_type="process",
            input_info=input_info or {},
            output_info=output_info or {},
            analysis_time=analysis_time,
            metadata=metadata or {}
        )
        self.entries.append(entry)
        logger.debug(f"[工作流日志] {module_name}.{step_name} - 处理完成，用时: {analysis_time:.2f}秒")
    
    def log_communication(self, module_name: str, step_name: str,
                         communication_time: float, information_delay: float = 0.0,
                         input_info: Optional[Dict[str, Any]] = None,
                         output_info: Optional[Dict[str, Any]] = None,
                         metadata: Optional[Dict[str, Any]] = None):
        """
        记录通讯过程
        
        Args:
            module_name: 模块名称
            step_name: 步骤名称
            communication_time: 通讯用时（秒）
            information_delay: 信息延迟（秒）
            input_info: 输入信息
            output_info: 输出信息
            metadata: 元数据
        """
        entry = WorkflowLogEntry(
            module_name=module_name,
            step_name=step_name,
            operation_type="communication",
            input_info=input_info or {},
            output_info=output_info or {},
            communication_time=communication_time,
            information_delay=information_delay,
            metadata=metadata or {}
        )
        self.entries.append(entry)
        logger.debug(f"[工作流日志] {module_name}.{step_name} - 通讯完成，用时: {communication_time:.2f}秒，延迟: {information_delay:.2f}秒")
    
    def log_output(self, module_name: str, step_name: str, output_info: Dict[str, Any],
                   metadata: Optional[Dict[str, Any]] = None):
        """
        记录输出信息
        
        Args:
            module_name: 模块名称
            step_name: 步骤名称
            output_info: 输出信息
            metadata: 元数据
        """
        entry = WorkflowLogEntry(
            module_name=module_name,
            step_name=step_name,
            operation_type="output",
            output_info=output_info,
            metadata=metadata or {}
        )
        self.entries.append(entry)
        logger.debug(f"[工作流日志] {module_name}.{step_name} - 输出信息已记录")
    
    def save(self):
        """保存日志到文件"""
        try:
            log_data = {
                "query": self.current_query,
                "total_entries": len(self.entries),
                "entries": [asdict(entry) for entry in self.entries],
                "summary": self._generate_summary()
            }
            
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"工作流日志已保存到: {self.log_file}")
        except Exception as e:
            logger.exception(f"保存工作流日志失败: {str(e)}")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成日志摘要"""
        total_communication_time = sum(entry.communication_time for entry in self.entries)
        total_analysis_time = sum(entry.analysis_time for entry in self.entries)
        total_information_delay = sum(entry.information_delay for entry in self.entries)
        
        module_stats = {}
        for entry in self.entries:
            if entry.module_name not in module_stats:
                module_stats[entry.module_name] = {
                    "communication_time": 0.0,
                    "analysis_time": 0.0,
                    "information_delay": 0.0,
                    "entry_count": 0
                }
            module_stats[entry.module_name]["communication_time"] += entry.communication_time
            module_stats[entry.module_name]["analysis_time"] += entry.analysis_time
            module_stats[entry.module_name]["information_delay"] += entry.information_delay
            module_stats[entry.module_name]["entry_count"] += 1
        
        return {
            "total_communication_time": total_communication_time,
            "total_analysis_time": total_analysis_time,
            "total_information_delay": total_information_delay,
            "module_stats": module_stats
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取日志摘要"""
        return self._generate_summary()


# 全局工作流日志记录器实例
_global_logger: Optional[WorkflowLogger] = None


def get_workflow_logger() -> WorkflowLogger:
    """获取全局工作流日志记录器"""
    global _global_logger
    if _global_logger is None:
        _global_logger = WorkflowLogger()
    return _global_logger


def reset_workflow_logger(log_file: Optional[str] = None):
    """重置全局工作流日志记录器"""
    global _global_logger
    _global_logger = WorkflowLogger(log_file)
    return _global_logger

