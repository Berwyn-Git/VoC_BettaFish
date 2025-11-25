"""
直接将HTML文件导出为PDF，保持与浏览器完全一致的格式
"""
import os
import sys
from loguru import logger

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.pdf_export import html_to_pdf_direct

def export_html_file_to_pdf(html_file_path: str, output_path: str = None) -> str:
    """直接将HTML文件导出为PDF，保持与浏览器完全一致的格式"""
    if not os.path.exists(html_file_path):
        logger.error(f"HTML文件不存在: {html_file_path}")
        return None
    
    try:
        # 确定输出路径
        if output_path is None:
            base_name = os.path.basename(html_file_path)
            output_path = os.path.splitext(base_name)[0] + ".pdf"
            output_path = os.path.join(os.path.dirname(os.path.abspath(html_file_path)), output_path)
        
        logger.info(f"开始将HTML直接转换为PDF: {html_file_path} -> {output_path}")
        
        # 直接HTML转PDF（保持与浏览器完全一致的格式）
        success = html_to_pdf_direct(html_file_path, output_path)
        
        if success and os.path.exists(output_path):
            logger.info(f"✅ PDF文件已成功生成: {output_path}")
            return output_path
        else:
            logger.error("PDF生成失败")
            return None
            
    except Exception as e:
        logger.exception(f"导出PDF失败: {str(e)}")
        return None

if __name__ == "__main__":
    # HTML文件路径
    html_file = "final_report_2025年蔚来ES8在最新的改款之后定单这么多还持续保持呢_20251126_051700.html"
    
    if not os.path.exists(html_file):
        logger.error(f"HTML文件不存在: {html_file}")
        sys.exit(1)
    
    # 导出PDF
    pdf_path = export_html_file_to_pdf(html_file)
    
    if pdf_path:
        file_size = os.path.getsize(pdf_path)
        print(f"\n[SUCCESS] PDF文件已成功生成!")
        print(f"[FILE] 文件位置: {pdf_path}")
        print(f"[SIZE] 文件大小: {file_size} 字节 ({file_size/1024:.2f} KB)")
    else:
        print("\n[ERROR] PDF生成失败，请查看日志了解详情")
        sys.exit(1)

