"""
PDF导出工具模块
将Markdown报告转换为PDF格式
"""

import os
import tempfile
from pathlib import Path
from typing import Optional
from loguru import logger

# 初始化PDF导出功能标志
PDF_EXPORT_AVAILABLE = False
USE_WEASYPRINT = False
USE_REPORTLAB = False

# 尝试导入markdown
try:
    import markdown
    MARKDOWN_AVAILABLE = True
    logger.debug(f"markdown模块导入成功，版本: {getattr(markdown, '__version__', 'unknown')}")
except ImportError as e:
    MARKDOWN_AVAILABLE = False
    logger.warning(f"markdown模块未安装，PDF导出功能不可用，请安装: pip install markdown。错误详情: {str(e)}")
except Exception as e:
    MARKDOWN_AVAILABLE = False
    logger.warning(f"markdown模块导入失败: {str(e)}")

# 如果markdown可用，尝试导入PDF生成库
if MARKDOWN_AVAILABLE:
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        PDF_EXPORT_AVAILABLE = True
        USE_WEASYPRINT = True
        logger.info("使用 WeasyPrint 作为 PDF 导出引擎")
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
        except ImportError as import_err:
            PDF_EXPORT_AVAILABLE = False
            USE_WEASYPRINT = False
            USE_REPORTLAB = False
            logger.warning(f"PDF导出功能不可用。WeasyPrint错误: {str(e)}，ReportLab错误: {str(import_err)}。请安装: pip install markdown reportlab")
else:
    logger.warning("PDF导出功能不可用，请安装: pip install markdown reportlab")


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
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import re
    import platform
    
    # 注册中文字体
    chinese_font_name = 'ChineseFont'
    chinese_font_bold_name = 'ChineseFontBold'
    
    try:
        # Windows系统字体路径
        if platform.system() == 'Windows':
            # 尝试注册微软雅黑
            font_paths = [
                r'C:\Windows\Fonts\msyh.ttc',  # 微软雅黑
                r'C:\Windows\Fonts\simsun.ttc',  # 宋体
                r'C:\Windows\Fonts\simhei.ttf',  # 黑体
            ]
            
            font_registered = False
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        # 注册常规字体
                        pdfmetrics.registerFont(TTFont(chinese_font_name, font_path))
                        # 尝试注册粗体（某些字体文件可能不支持）
                        try:
                            pdfmetrics.registerFont(TTFont(chinese_font_bold_name, font_path))
                        except:
                            chinese_font_bold_name = chinese_font_name  # 如果粗体注册失败，使用常规字体
                        font_registered = True
                        logger.info(f"成功注册中文字体: {font_path}")
                        break
                    except Exception as e:
                        logger.warning(f"注册字体失败 {font_path}: {str(e)}")
                        continue
            
            if not font_registered:
                logger.warning("无法注册中文字体，将使用默认字体（可能无法正确显示中文）")
                chinese_font_name = 'Helvetica'  # 回退到默认字体
                chinese_font_bold_name = 'Helvetica-Bold'
        else:
            # Linux/Mac系统，尝试使用系统字体
            logger.warning("非Windows系统，尝试使用默认字体")
            chinese_font_name = 'Helvetica'
            chinese_font_bold_name = 'Helvetica-Bold'
    except Exception as e:
        logger.warning(f"字体注册过程出错: {str(e)}，使用默认字体")
        chinese_font_name = 'Helvetica'
        chinese_font_bold_name = 'Helvetica-Bold'
    
    # 创建 PDF 文档
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    
    # 获取样式
    styles = getSampleStyleSheet()
    
    # 创建自定义样式（使用中文字体）
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=chinese_font_bold_name,
        fontSize=24,
        spaceAfter=12,
        textColor='#000000',
        alignment=TA_LEFT
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontName=chinese_font_bold_name,
        fontSize=18,
        spaceAfter=10,
        textColor='#000000',
        alignment=TA_LEFT
    )
    
    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontName=chinese_font_bold_name,
        fontSize=14,
        spaceAfter=8,
        textColor='#000000',
        alignment=TA_LEFT
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=chinese_font_name,
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
            
            # 先转义 & 符号
            content = content.replace('&', '&amp;')
            
            # 处理Markdown格式
            # 加粗：使用<b>标签，ReportLab会自动使用粗体字体（已在heading样式中设置）
            content = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', content)
            # 斜体
            content = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', content)
            # 代码
            content = re.sub(r'`(.+?)`', r'<font name="Courier">\1</font>', content)
            
            # 转义HTML标签（但保留ReportLab支持的标签）
            # 先保护已处理的标签
            protected_tags = {
                '<b>': '___BOLD_START___',
                '</b>': '___BOLD_END___',
                '<i>': '___ITALIC_START___',
                '</i>': '___ITALIC_END___',
                '<font name="Courier">': '___CODE_START___',
                '</font>': '___CODE_END___'
            }
            
            for tag, placeholder in protected_tags.items():
                content = content.replace(tag, placeholder)
            
            # 转义所有剩余的 < 和 >
            content = content.replace('<', '&lt;').replace('>', '&gt;')
            
            # 恢复已处理的标签
            for tag, placeholder in protected_tags.items():
                content = content.replace(placeholder, tag)
            
            story.append(Paragraph(content, normal_style))
        else:
            # 空行
            story.append(Spacer(1, 0.2*cm))
    
    # 构建 PDF
    doc.build(story)
    
    logger.info(f"PDF已成功生成（ReportLab）: {output_path}")
    return True


def html_to_pdf_direct(html_file_path: str, output_path: str) -> bool:
    """
    直接将HTML文件转换为PDF，保持与浏览器完全一致的格式
    
    Args:
        html_file_path: HTML文件路径
        output_path: PDF输出路径
        
    Returns:
        是否成功生成PDF
    """
    if not os.path.exists(html_file_path):
        logger.error(f"HTML文件不存在: {html_file_path}")
        return False
    
    # 转换为绝对路径
    html_file_path = os.path.abspath(html_file_path)
    output_path = os.path.abspath(output_path)
    
    logger.info(f"开始直接HTML转PDF: {html_file_path} -> {output_path}")
    
    # 方法1: 尝试使用playwright（最佳选择，完全保留样式）
    try:
        from playwright.sync_api import sync_playwright
        logger.info("使用 playwright 生成PDF...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 加载HTML文件
            html_url = f"file:///{html_file_path.replace(os.sep, '/')}"
            logger.info(f"加载HTML: {html_url}")
            page.goto(html_url, wait_until='networkidle', timeout=60000)
            
            # 等待页面完全加载
            import time
            time.sleep(2)
            
            # 生成PDF
            page.pdf(
                path=output_path,
                format='A4',
                margin={
                    'top': '0.75in',
                    'right': '0.75in',
                    'bottom': '0.75in',
                    'left': '0.75in'
                },
                print_background=True,  # 保留背景色和图片
                prefer_css_page_size=False
            )
            
            browser.close()
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logger.info(f"✅ PDF已成功生成（playwright）: {output_path}, 大小: {file_size} 字节")
            return True
        else:
            logger.error("playwright生成失败，文件不存在")
            return False
    except ImportError:
        logger.warning("playwright未安装，跳过")
    except Exception as e:
        logger.exception(f"playwright失败: {str(e)}")
    
    # 方法2: 尝试使用pdfkit + wkhtmltopdf
    try:
        import pdfkit
        logger.info("使用 pdfkit + wkhtmltopdf 生成PDF...")
        
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None,
        }
        
        html_url = f"file:///{html_file_path.replace(os.sep, '/')}"
        pdfkit.from_url(html_url, output_path, options=options)
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logger.info(f"✅ PDF已成功生成（pdfkit）: {output_path}, 大小: {file_size} 字节")
            return True
        else:
            logger.error("pdfkit生成失败，文件不存在")
            return False
    except ImportError:
        logger.warning("pdfkit未安装，跳过")
    except Exception as e:
        logger.exception(f"pdfkit失败: {str(e)}")
    
    logger.error("所有HTML转PDF方法都失败")
    return False


def export_report_to_pdf(report_content: str, output_dir: str, query: str, engine_name: str = "market") -> Optional[str]:
    """
    导出报告为PDF文件
    
    Args:
        report_content: Markdown格式的报告内容
        output_dir: 输出目录（相对路径或绝对路径）
        query: 查询内容（用于生成文件名）
        engine_name: 引擎名称（market/customer/compete）
        
    Returns:
        PDF文件路径（绝对路径），如果失败返回None
    """
    if not PDF_EXPORT_AVAILABLE:
        logger.error("PDF导出功能不可用")
        return None
    
    try:
        from datetime import datetime
        
        # 验证报告内容
        if not report_content or not report_content.strip():
            logger.error("报告内容为空，无法生成PDF")
            return None
        
        logger.info(f"开始导出PDF - 引擎: {engine_name}, 内容长度: {len(report_content)} 字符")
        
        # 确保输出目录是绝对路径（相对于项目根目录）
        if not os.path.isabs(output_dir):
            # 获取项目根目录（utils目录的父目录）
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_file_dir)
            output_dir = os.path.join(project_root, output_dir)
            logger.info(f"相对路径转换为绝对路径: {output_dir}")
        else:
            logger.info(f"使用绝对路径: {output_dir}")
        
        # 确保输出目录存在
        try:
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"PDF输出目录已确认存在: {output_dir}")
        except Exception as e:
            logger.error(f"创建输出目录失败: {output_dir}, 错误: {str(e)}")
            return None
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_safe = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
        query_safe = query_safe.replace(' ', '_')[:30]
        if not query_safe:
            query_safe = "report"
        
        # 引擎名称映射
        engine_names = {
            'market': '市场分析',
            'customer': '用户分析',
            'compete': '竞争分析',
            'report': '汇总报告'
        }
        engine_display = engine_names.get(engine_name, engine_name)
        
        filename = f"{engine_display}_报告_{query_safe}_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)
        filepath = os.path.abspath(filepath)  # 确保是绝对路径
        
        logger.info(f"正在生成PDF文件: {filepath}")
        
        # 生成PDF
        title = f"{engine_display}报告 - {query}"
        logger.info(f"调用 markdown_to_pdf，标题: {title}")
        
        success = markdown_to_pdf(report_content, filepath, title)
        
        if success:
            logger.info(f"markdown_to_pdf 返回成功")
            # 验证文件是否存在
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                logger.info(f"PDF文件已成功生成: {filepath}, 大小: {file_size} 字节")
                return filepath
            else:
                logger.error(f"PDF文件生成失败：文件不存在 {filepath}")
                # 检查目录权限
                if os.access(output_dir, os.W_OK):
                    logger.error(f"目录可写，但文件未生成")
                else:
                    logger.error(f"目录不可写: {output_dir}")
                return None
        else:
            logger.error(f"PDF生成失败: markdown_to_pdf 返回 False")
            return None
            
    except Exception as e:
        logger.exception(f"导出PDF失败: {str(e)}")
        import traceback
        logger.error(f"详细错误信息:\n{traceback.format_exc()}")
        return None

