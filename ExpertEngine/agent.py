"""
Expert Agent主类
功能：对输出观点进行批注和修改
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from loguru import logger

from .llms import LLMClient
from .nodes import ExpertReviewNode
from .state import ExpertState
from .utils.config import settings, Settings
from config import settings as global_settings


class ExpertAgent:
    """Expert Agent主类 - 对输出观点进行批注和修改"""
    
    def __init__(self, config: Optional[Settings] = None):
        """
        初始化Expert Agent
        
        Args:
            config: 可选配置对象（不填则用全局settings）
        """
        # 如果提供了config则使用，否则使用ExpertEngine的settings，并尝试从全局config获取
        if config is None:
            # 使用ExpertEngine的settings，并从全局config获取fallback配置
            self.config = settings
            # 如果ExpertEngine配置为空，尝试从全局配置获取
            if not self.config.EXPERT_ENGINE_API_KEY:
                self.config.EXPERT_ENGINE_API_KEY = getattr(global_settings, 'EXPERT_ENGINE_API_KEY', None) or getattr(global_settings, 'REPORT_ENGINE_API_KEY', None)
            if not self.config.EXPERT_ENGINE_BASE_URL:
                self.config.EXPERT_ENGINE_BASE_URL = getattr(global_settings, 'EXPERT_ENGINE_BASE_URL', None) or getattr(global_settings, 'REPORT_ENGINE_BASE_URL', None)
            if not self.config.EXPERT_ENGINE_MODEL_NAME:
                self.config.EXPERT_ENGINE_MODEL_NAME = getattr(global_settings, 'EXPERT_ENGINE_MODEL_NAME', None) or getattr(global_settings, 'REPORT_ENGINE_MODEL_NAME', None)
        else:
            # 如果传入的是其他Engine的config（如ReportEngine），需要创建一个新的Settings实例
            # 因为不同Engine的Settings类字段不同
            self.config = settings
            # 从传入的config中尝试获取REPORT_ENGINE配置作为fallback
            if hasattr(config, 'REPORT_ENGINE_API_KEY'):
                if not self.config.EXPERT_ENGINE_API_KEY:
                    self.config.EXPERT_ENGINE_API_KEY = getattr(config, 'REPORT_ENGINE_API_KEY', None)
                if not self.config.EXPERT_ENGINE_BASE_URL:
                    self.config.EXPERT_ENGINE_BASE_URL = getattr(config, 'REPORT_ENGINE_BASE_URL', None)
                if not self.config.EXPERT_ENGINE_MODEL_NAME:
                    self.config.EXPERT_ENGINE_MODEL_NAME = getattr(config, 'REPORT_ENGINE_MODEL_NAME', None)
            # 同时从全局配置获取
            if not self.config.EXPERT_ENGINE_API_KEY:
                self.config.EXPERT_ENGINE_API_KEY = getattr(global_settings, 'EXPERT_ENGINE_API_KEY', None) or getattr(global_settings, 'REPORT_ENGINE_API_KEY', None)
            if not self.config.EXPERT_ENGINE_BASE_URL:
                self.config.EXPERT_ENGINE_BASE_URL = getattr(global_settings, 'EXPERT_ENGINE_BASE_URL', None) or getattr(global_settings, 'REPORT_ENGINE_BASE_URL', None)
            if not self.config.EXPERT_ENGINE_MODEL_NAME:
                self.config.EXPERT_ENGINE_MODEL_NAME = getattr(global_settings, 'EXPERT_ENGINE_MODEL_NAME', None) or getattr(global_settings, 'REPORT_ENGINE_MODEL_NAME', None)
        
        # 初始化LLM客户端
        self.llm_client = self._initialize_llm()
        
        # 初始化节点
        self._initialize_nodes()
        
        # 状态
        self.state = ExpertState()
        
        # 确保输出目录存在
        os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)
        
        logger.info(f"Expert Agent已初始化")
        logger.info(f"使用LLM: {self.llm_client.get_model_info()}")
    
    def _initialize_llm(self) -> LLMClient:
        """初始化LLM客户端"""
        # 优先使用ExpertEngine配置，如果未配置则使用ReportEngine配置
        api_key = (self.config.EXPERT_ENGINE_API_KEY or 
                  getattr(global_settings, 'EXPERT_ENGINE_API_KEY', None) or 
                  getattr(global_settings, 'REPORT_ENGINE_API_KEY', None))
        model_name = (self.config.EXPERT_ENGINE_MODEL_NAME or 
                     getattr(global_settings, 'EXPERT_ENGINE_MODEL_NAME', None) or 
                     getattr(global_settings, 'REPORT_ENGINE_MODEL_NAME', None) or
                     "gemini-2.5-pro")  # 默认模型
        base_url = (self.config.EXPERT_ENGINE_BASE_URL or 
                   getattr(global_settings, 'EXPERT_ENGINE_BASE_URL', None) or 
                   getattr(global_settings, 'REPORT_ENGINE_BASE_URL', None) or
                   "https://aihubmix.com/v1")  # 默认base_url
        return LLMClient(
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
        )
    
    def _initialize_nodes(self):
        """初始化处理节点"""
        self.expert_review_node = ExpertReviewNode(self.llm_client)
    
    def review_and_annotate(self, report_content: str, business_rules: str = "", 
                           save_result: bool = True) -> Dict[str, Any]:
        """
        对报告内容进行专家批注和修改
        
        Args:
            report_content: 待批注的报告内容
            business_rules: 业务逻辑要求（可选，目前先留空）
            save_result: 是否保存结果到文件
            
        Returns:
            包含批注和修改后的报告内容
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"开始专家批注和修改")
        logger.info(f"{'='*60}")
        
        try:
            # Step 1: 专家批注和修改
            reviewed_content = self._expert_review(report_content, business_rules)
            
            # Step 2: 保存结果
            saved_files = {}
            if save_result:
                saved_files = self._save_result(reviewed_content)
            
            logger.info("专家批注和修改完成！")
            
            return {
                'reviewed_content': reviewed_content,
                **saved_files
            }
            
        except Exception as e:
            logger.exception(f"专家批注过程中发生错误: {str(e)}")
            raise e
    
    def _expert_review(self, report_content: str, business_rules: str) -> str:
        """执行专家批注和修改"""
        logger.info("执行专家批注和修改...")
        
        # 准备输入数据
        review_input = {
            "report_content": report_content,
            "business_rules": business_rules or "暂无特定业务逻辑要求，请根据通用专业标准进行批注和修改。"
        }
        
        # 调用专家批注节点
        reviewed_content = self.expert_review_node.run(review_input)
        
        # 更新状态
        self.state.reviewed_content = reviewed_content
        self.state.mark_completed()
        
        logger.info("专家批注和修改完成")
        return reviewed_content
    
    def _save_result(self, reviewed_content: str):
        """保存批注结果到文件"""
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_safe = "".join(c for c in self.state.query if c.isalnum() or c in (' ', '-', '_')).rstrip()
        query_safe = query_safe.replace(' ', '_')[:30] if query_safe else "expert_review"
        
        filename = f"expert_review_{query_safe}_{timestamp}.md"
        filepath = os.path.join(self.config.OUTPUT_DIR, filename)
        
        # 保存批注结果
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(reviewed_content)
        
        logger.info(f"批注结果已保存到: {filepath}")
        
        return {
            'reviewed_filename': filename,
            'reviewed_filepath': os.path.abspath(filepath)
        }
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """获取进度摘要"""
        return self.state.to_dict()
    
    def load_state(self, filepath: str):
        """从文件加载状态"""
        self.state = ExpertState.load_from_file(filepath)
        logger.info(f"状态已从 {filepath} 加载")
    
    def save_state(self, filepath: str):
        """保存状态到文件"""
        self.state.save_to_file(filepath)
        logger.info(f"状态已保存到 {filepath}")


def create_agent(config_file: Optional[str] = None) -> ExpertAgent:
    """
    创建Expert Agent实例的便捷函数
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        ExpertAgent实例
    """
    config = Settings()
    return ExpertAgent(config)

