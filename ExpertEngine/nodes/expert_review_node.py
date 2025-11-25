"""
专家批注节点
对报告内容进行批注和修改
"""

from typing import Dict, Any
from loguru import logger

from .base_node import BaseNode
from ..llms.base import LLMClient
from ..prompts import SYSTEM_PROMPT_EXPERT_REVIEW


class ExpertReviewNode(BaseNode):
    """专家批注处理节点"""
    
    def __init__(self, llm_client: LLMClient):
        """
        初始化专家批注节点
        
        Args:
            llm_client: LLM客户端
        """
        super().__init__(llm_client, "ExpertReviewNode")
    
    def run(self, input_data: Dict[str, Any], **kwargs) -> str:
        """
        执行专家批注和修改
        
        Args:
            input_data: 包含报告内容和业务规则的字典
                - report_content: 待批注的报告内容
                - business_rules: 业务逻辑要求（可选）
                
        Returns:
            批注和修改后的报告内容
        """
        logger.info("开始专家批注和修改...")
        
        try:
            report_content = input_data.get('report_content', '')
            business_rules = input_data.get('business_rules', '暂无特定业务逻辑要求，请根据通用专业标准进行批注和修改。')
            
            # 准备LLM输入
            user_prompt = f"""请对以下报告内容进行专家批注和修改：

**报告内容：**
{report_content}

**业务逻辑要求：**
{business_rules}

请根据业务逻辑要求和专业标准，对报告中的观点进行批注和修改。"""
            
            # 调用LLM进行批注
            response = self.llm_client.stream_invoke_to_string(SYSTEM_PROMPT_EXPERT_REVIEW, user_prompt)
            
            # 处理响应
            processed_response = self.process_output(response)
            
            logger.info("专家批注和修改完成")
            return processed_response
            
        except Exception as e:
            logger.exception(f"专家批注失败: {str(e)}")
            # 返回原始内容
            return input_data.get('report_content', '')
    
    def process_output(self, output: str) -> str:
        """
        处理LLM输出
        
        Args:
            output: LLM原始输出
            
        Returns:
            处理后的批注内容
        """
        try:
            logger.info(f"处理LLM原始输出，长度: {len(output)} 字符")
            
            reviewed_content = output.strip()
            
            # 清理markdown代码块标记（如果存在）
            if reviewed_content.startswith('```markdown'):
                reviewed_content = reviewed_content[11:]
                if reviewed_content.endswith('```'):
                    reviewed_content = reviewed_content[:-3]
            elif reviewed_content.startswith('```'):
                reviewed_content = reviewed_content[3:]
                if reviewed_content.endswith('```'):
                    reviewed_content = reviewed_content[:-3]
            
            reviewed_content = reviewed_content.strip()
            
            if not reviewed_content:
                logger.info("处理后内容为空，返回原始输出")
                return output
            
            logger.info(f"批注处理完成，最终长度: {len(reviewed_content)} 字符")
            return reviewed_content
            
        except Exception as e:
            logger.exception(f"处理批注输出失败: {str(e)}，返回原始输出")
            return output

