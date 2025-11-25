"""
直接将HTML文件导出为PDF，保持与浏览器完全一致的格式
"""
import os
import sys
from loguru import logger

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def export_html_to_pdf_direct(html_file_path: str, output_path: str = None) -> str:
    """
    直接将HTML文件转换为PDF，保持与浏览器完全一致的格式
    
    优先使用的方法：
    1. pdfkit + wkhtmltopdf（需要安装wkhtmltopdf）
    2. playwright（需要安装playwright和浏览器）
    3. selenium + Chrome（需要安装selenium和ChromeDriver）
    """
    if not os.path.exists(html_file_path):
        logger.error(f"HTML文件不存在: {html_file_path}")
        return None
    
    # 确定输出路径
    if output_path is None:
        base_name = os.path.basename(html_file_path)
        output_path = os.path.splitext(base_name)[0] + ".pdf"
        output_path = os.path.join(os.path.dirname(html_file_path), output_path)
    
    # 转换为绝对路径
    html_file_path = os.path.abspath(html_file_path)
    output_path = os.path.abspath(output_path)
    
    logger.info(f"HTML文件: {html_file_path}")
    logger.info(f"输出PDF: {output_path}")
    
    # 方法1: 尝试使用pdfkit + wkhtmltopdf
    try:
        import pdfkit
        logger.info("尝试使用 pdfkit + wkhtmltopdf...")
        
        # 配置选项
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None,  # 允许访问本地文件（CSS、图片等）
        }
        
        # 转换为file:// URL
        html_url = f"file:///{html_file_path.replace(os.sep, '/')}"
        
        pdfkit.from_url(html_url, output_path, options=options)
        
        if os.path.exists(output_path):
            logger.info(f"✅ PDF已成功生成（pdfkit）: {output_path}")
            return output_path
        else:
            logger.warning("pdfkit生成失败，文件不存在")
    except ImportError:
        logger.info("pdfkit未安装，跳过")
    except Exception as e:
        logger.warning(f"pdfkit失败: {str(e)}")
    
    # 方法2: 尝试使用playwright
    try:
        from playwright.sync_api import sync_playwright
        logger.info("尝试使用 playwright...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 加载HTML文件
            html_url = f"file:///{html_file_path.replace(os.sep, '/')}"
            page.goto(html_url, wait_until='networkidle')
            
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
                print_background=True  # 保留背景色和图片
            )
            
            browser.close()
        
        if os.path.exists(output_path):
            logger.info(f"✅ PDF已成功生成（playwright）: {output_path}")
            return output_path
        else:
            logger.warning("playwright生成失败，文件不存在")
    except ImportError:
        logger.info("playwright未安装，跳过")
    except Exception as e:
        logger.warning(f"playwright失败: {str(e)}")
    
    # 方法3: 尝试使用selenium + Chrome
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        logger.info("尝试使用 selenium + Chrome...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # 设置打印选项
        chrome_options.add_experimental_option('prefs', {
            'printing.print_preview_sticky_settings.appState': '{"recentDestinations":[{"id":"Save as PDF","origin":"local","account":""}],"selectedDestinationId":"Save as PDF","version":2}'
        })
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # 加载HTML文件
        html_url = f"file:///{html_file_path.replace(os.sep, '/')}"
        driver.get(html_url)
        
        # 等待页面加载
        import time
        time.sleep(2)
        
        # 使用Chrome的打印功能（需要手动处理）
        # 注意：selenium不能直接生成PDF，需要配合其他工具
        logger.warning("selenium需要配合其他工具才能生成PDF，跳过")
        driver.quit()
    except ImportError:
        logger.info("selenium未安装，跳过")
    except Exception as e:
        logger.warning(f"selenium失败: {str(e)}")
    
    # 如果所有方法都失败，提示用户
    logger.error("所有PDF生成方法都失败，请安装以下工具之一：")
    logger.error("1. pdfkit + wkhtmltopdf: pip install pdfkit，然后下载安装 wkhtmltopdf")
    logger.error("2. playwright: pip install playwright，然后运行 playwright install chromium")
    logger.error("3. 或者使用浏览器的打印功能（Ctrl+P -> 保存为PDF）")
    
    return None

if __name__ == "__main__":
    # HTML文件路径
    html_file = "final_report_2025年蔚来ES8在最新的改款之后定单这么多还持续保持呢_20251126_051700.html"
    
    if not os.path.exists(html_file):
        logger.error(f"HTML文件不存在: {html_file}")
        sys.exit(1)
    
    # 导出PDF
    pdf_path = export_html_to_pdf_direct(html_file)
    
    if pdf_path:
        file_size = os.path.getsize(pdf_path)
        print(f"\n[SUCCESS] PDF文件已成功生成!")
        print(f"[FILE] 文件位置: {pdf_path}")
        print(f"[SIZE] 文件大小: {file_size} 字节 ({file_size/1024:.2f} KB)")
    else:
        print("\n[ERROR] PDF生成失败")
        print("\n建议安装以下工具之一：")
        print("1. pdfkit + wkhtmltopdf:")
        print("   pip install pdfkit")
        print("   然后从 https://wkhtmltopdf.org/downloads.html 下载安装 wkhtmltopdf")
        print("\n2. playwright:")
        print("   pip install playwright")
        print("   playwright install chromium")
        sys.exit(1)

