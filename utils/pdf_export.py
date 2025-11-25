"""
PDF导出工具模块
将Markdown报告转换为PDF格式
"""

import os
import tempfile
from pathlib import Path
from typing import Optional
from loguru import logger

try:
    import markdown
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        PDF_EXPORT_AVAILABLE = True
        USE_WEASYPRINT = True
    except (ImportError, OSError) as e:
        # WeasyPrint 在 Windows 上可能需要 GTK+ 运行时库
        # 尝试使用 reportlab 作为备选方案
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            PDF_EXPORT_AVAILABLE = True
            USE_WEASYPRINT = False
            USE_REPORTLAB = True
            logger.info("使用 reportlab 作为 PDF 导出引擎（WeasyPrint 不可用）")
        except ImportError:
            PDF_EXPORT_AVAILABLE = False
            USE_WEASYPRINT = False
            USE_REPORTLAB = False
            logger.warning(f"PDF导出功能不可用。WeasyPrint错误: {str(e)}。请安装: pip install markdown weasyprint 或 pip install reportlab")
except ImportError:
    PDF_EXPORT_AVAILABLE = False
    USE_WEASYPRINT = False
    USE_REPORTLAB = False
    logger.warning("PDF导出功能不可用，请安装: pip install markdown")


def markdown_to_pdf(markdown_content: str, output_path: str, title: str = "报告") -> bool:
    """
    将Markdown内容转换为PDF文件
    
    Args:
        markdown_content: Markdown格式的报告内容
        output_path: PDF输出路径
        title: PDF标题
        
    Returns:
        是否成功生成PDF
    """
    if not PDF_EXPORT_AVAILABLE:
        logger.error("PDF导出功能不可用")
        return False
    
    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        if USE_WEASYPRINT:
            # 使用 WeasyPrint（需要 GTK+ 运行时库）
            return _markdown_to_pdf_weasyprint(markdown_content, output_path, title)
        elif USE_REPORTLAB:
            # 使用 ReportLab（纯 Python，Windows 友好）
            return _markdown_to_pdf_reportlab(markdown_content, output_path, title)
        else:
            logger.error("没有可用的 PDF 导出引擎")
            return False
        
    except Exception as e:
        logger.exception(f"PDF生成失败: {str(e)}")
        return False


def _markdown_to_pdf_weasyprint(markdown_content: str, output_path: str, title: str) -> bool:
    """使用 WeasyPrint 生成 PDF"""
    # 将Markdown转换为HTML
    html_content = markdown.markdown(
        markdown_content,
        extensions=['extra', 'codehilite', 'tables', 'toc']
    )
    
    # 构建完整的HTML文档
    full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}
        body {{
            font-family: "Microsoft YaHei", "SimSun", "Arial", sans-serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            font-size: 24pt;
            margin-top: 20pt;
            margin-bottom: 12pt;
            page-break-after: avoid;
        }}
        h2 {{
            font-size: 18pt;
            margin-top: 16pt;
            margin-bottom: 10pt;
            page-break-after: avoid;
        }}
        h3 {{
            font-size: 14pt;
            margin-top: 12pt;
            margin-bottom: 8pt;
            page-break-after: avoid;
        }}
        p {{
            margin-top: 6pt;
            margin-bottom: 6pt;
            text-align: justify;
        }}
        ul, ol {{
            margin-top: 6pt;
            margin-bottom: 6pt;
            padding-left: 24pt;
        }}
        li {{
            margin-top: 3pt;
            margin-bottom: 3pt;
        }}
        code {{
            font-family: "Consolas", "Monaco", monospace;
            font-size: 10pt;
            background-color: #f5f5f5;
            padding: 2pt 4pt;
            border-radius: 3pt;
        }}
        pre {{
            background-color: #f5f5f5;
            padding: 10pt;
            border-radius: 5pt;
            overflow-x: auto;
            page-break-inside: avoid;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10pt;
            margin-bottom: 10pt;
            page-break-inside: avoid;
        }}
        th, td {{
            border: 1pt solid #ddd;
            padding: 8pt;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        blockquote {{
            border-left: 4pt solid #ddd;
            margin-left: 0;
            padding-left: 12pt;
            color: #666;
            font-style: italic;
        }}
        .page-break {{
            page-break-before: always;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
"""
    
    # 使用WeasyPrint生成PDF
    font_config = FontConfiguration()
    HTML(string=full_html).write_pdf(
        output_path,
        font_config=font_config
    )
    
    logger.info(f"PDF已成功生成（WeasyPrint）: {output_path}")
    return True


def _markdown_to_pdf_reportlab(markdown_content: str, output_path: str, title: str) -> bool:
    """使用 ReportLab 生成 PDF（Windows 友好）"""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
    import re
    
    # 创建 PDF 文档
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    
    # 获取样式
    styles = getSampleStyleSheet()
    
    # 创建自定义样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=12,
        textColor='#000000',
        alignment=TA_LEFT
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=10,
        textColor='#000000',
        alignment=TA_LEFT
    )
    
    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=8,
        textColor='#000000',
        alignment=TA_LEFT
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6,
        textColor='#333333',
        alignment=TA_JUSTIFY,
        leading=18
    )
    
    code_style = ParagraphStyle(
        'CustomCode',
        parent=styles['Code'],
        fontSize=10,
        fontName='Courier',
        backColor='#f5f5f5',
        borderPadding=4,
        leftIndent=10,
        rightIndent=10
    )
    
    # 构建内容
    story = []
    
    # 添加标题
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # 简单的 Markdown 解析（处理基本格式）
    lines = markdown_content.split('\n')
    in_code_block = False
    code_block_content = []
    
    for line in lines:
        line = line.strip()
        
        # 处理代码块
        if line.startswith('```'):
            if in_code_block:
                # 结束代码块
                if code_block_content:
                    story.append(Preformatted('\n'.join(code_block_content), code_style))
                    story.append(Spacer(1, 0.3*cm))
                code_block_content = []
                in_code_block = False
            else:
                in_code_block = True
            continue
        
        if in_code_block:
            code_block_content.append(line)
            continue
        
        # 处理标题
        if line.startswith('# '):
            story.append(Paragraph(line[2:], title_style))
            story.append(Spacer(1, 0.3*cm))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], heading2_style))
            story.append(Spacer(1, 0.2*cm))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], heading3_style))
            story.append(Spacer(1, 0.2*cm))
        elif line.startswith('- ') or line.startswith('* '):
            # 列表项
            content = line[2:].strip()
            # 简单的 HTML 转义
            content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(f"• {content}", normal_style))
        elif line:
            # 普通段落
            # 简单的 Markdown 格式处理
            content = line
            # 加粗
            content = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', content)
            # 斜体
            content = re.sub(r'\*(.+?)\*', r'<i>\1</i>', content)
            # 代码
            content = re.sub(r'`(.+?)`', r'<font name="Courier">\1</font>', content)
            # HTML 转义
            content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # 恢复已处理的标签
            content = content.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
            content = content.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
            content = content.replace('&lt;font name="Courier"&gt;', '<font name="Courier">')
            content = content.replace('&lt;/font&gt;', '</font>')
            
            story.append(Paragraph(content, normal_style))
        else:
            # 空行
            story.append(Spacer(1, 0.2*cm))
    
    # 构建 PDF
    doc.build(story)
    
    logger.info(f"PDF已成功生成（ReportLab）: {output_path}")
    return True


def export_report_to_pdf(report_content: str, output_dir: str, query: str, engine_name: str = "market") -> Optional[str]:
    """
    导出报告为PDF文件
    
    Args:
        report_content: Markdown格式的报告内容
        output_dir: 输出目录
        query: 查询内容（用于生成文件名）
        engine_name: 引擎名称（market/customer/compete）
        
    Returns:
        PDF文件路径，如果失败返回None
    """
    if not PDF_EXPORT_AVAILABLE:
        logger.error("PDF导出功能不可用")
        return None
    
    try:
        from datetime import datetime
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_safe = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
        query_safe = query_safe.replace(' ', '_')[:30]
        
        # 引擎名称映射
        engine_names = {
            'market': '市场分析',
            'customer': '用户分析',
            'compete': '竞争分析'
        }
        engine_display = engine_names.get(engine_name, engine_name)
        
        filename = f"{engine_display}_报告_{query_safe}_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)
        
        # 生成PDF
        title = f"{engine_display}报告 - {query}"
        if markdown_to_pdf(report_content, filepath, title):
            return filepath
        else:
            return None
            
    except Exception as e:
        logger.exception(f"导出PDF失败: {str(e)}")
        return None

