"""
Report Engine Flask接口
提供HTTP API用于报告生成
"""

import os
import json
import threading
import time
from datetime import datetime
from flask import Blueprint, request, jsonify, Response, send_file
from typing import Dict, Any
from loguru import logger
from .agent import ReportAgent, create_agent
from .utils.config import settings


# 创建Blueprint
report_bp = Blueprint('report_engine', __name__)

# 全局变量
report_agent = None
current_task = None
task_lock = threading.Lock()


def initialize_report_engine():
    """初始化Report Engine"""
    global report_agent
    try:
        report_agent = create_agent()
        logger.info("Report Engine初始化成功")
        return True
    except Exception as e:
        logger.exception(f"Report Engine初始化失败: {str(e)}")
        return False


class ReportTask:
    """报告生成任务"""

    def __init__(self, query: str, task_id: str, custom_template: str = ""):
        self.task_id = task_id
        self.query = query
        self.custom_template = custom_template
        self.status = "pending"  # pending, running, completed, error
        self.progress = 0
        self.result = None
        self.error_message = ""
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.html_content = ""
        self.report_file_path = ""
        self.report_file_relative_path = ""
        self.report_file_name = ""
        self.state_file_path = ""
        self.state_file_relative_path = ""
        self.pdf_file_path = ""

    def update_status(self, status: str, progress: int = None, error_message: str = ""):
        """更新任务状态"""
        self.status = status
        if progress is not None:
            self.progress = progress
        if error_message:
            self.error_message = error_message
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'task_id': self.task_id,
            'query': self.query,
            'status': self.status,
            'progress': self.progress,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'has_result': bool(self.html_content),
            'report_file_ready': bool(self.report_file_path),
            'report_file_name': self.report_file_name,
            'report_file_path': self.report_file_relative_path,
            'pdf_file_path': self.pdf_file_path if hasattr(self, 'pdf_file_path') else ''
        }


def check_engines_ready() -> Dict[str, Any]:
    """检查三个子引擎是否都有新文件"""
    directories = {
        'market': 'market_engine_streamlit_reports',  # 市场分析
        'customer': 'customer_engine_streamlit_reports',  # 用户分析
        'compete': 'compete_engine_streamlit_reports'  # 竞争分析
    }

    forum_log_path = 'logs/forum.log'

    if not report_agent:
        return {
            'ready': False,
            'error': 'Report Engine未初始化'
        }

    return report_agent.check_input_files(
        directories['market'],  # 市场分析（原insight）
        directories['customer'],  # 用户分析（原media）
        directories['compete'],  # 竞争分析（原query）
        forum_log_path
    )


def run_report_generation(task: ReportTask, query: str, custom_template: str = ""):
    """在后台线程中运行报告生成"""
    global current_task

    try:
        task.update_status("running", 10)

        # 检查输入文件
        check_result = check_engines_ready()
        if not check_result['ready']:
            task.update_status("error", 0, f"输入文件未准备就绪: {check_result.get('missing_files', [])}")
            return

        task.update_status("running", 30)

        # 加载输入文件
        content = report_agent.load_input_files(check_result['latest_files'])

        task.update_status("running", 50)

        # 生成报告
        generation_result = report_agent.generate_report(
            query=query,
            reports=content['reports'],
            forum_logs=content['forum_logs'],
            custom_template=custom_template,
            save_report=True
        )

        html_report = generation_result.get('html_content', '')

        task.update_status("running", 90)

        # 保存结果
        task.html_content = html_report
        task.report_file_path = generation_result.get('report_filepath', '')
        task.report_file_relative_path = generation_result.get('report_relative_path', '')
        task.report_file_name = generation_result.get('report_filename', '')
        task.state_file_path = generation_result.get('state_filepath', '')
        task.state_file_relative_path = generation_result.get('state_relative_path', '')
        
        # 报告生成完成后，更新基准（将当前文件数量设为新基准）
        try:
            directories = {
                'market': 'market_engine_streamlit_reports',
                'customer': 'customer_engine_streamlit_reports',
                'compete': 'compete_engine_streamlit_reports'
            }
            report_agent.file_baseline.initialize_baseline(directories)
            logger.info("报告生成完成，已更新文件数量基准")
        except Exception as e:
            logger.warning(f"更新基准失败: {str(e)}")
        
        # 自动导出PDF报告（优先使用直接HTML转PDF）
        try:
            from utils.pdf_export import html_to_pdf_direct
            
            # 如果报告已保存为HTML文件，直接使用HTML文件
            if task.report_file_path and os.path.exists(task.report_file_path):
                html_file = task.report_file_path
                
                # 生成PDF文件名
                base_name = os.path.basename(html_file)
                pdf_filename = os.path.splitext(base_name)[0] + ".pdf"
                pdf_path = os.path.join(report_agent.config.OUTPUT_DIR, pdf_filename)
                pdf_path = os.path.abspath(pdf_path)
                
                logger.info(f"开始自动导出PDF（直接HTML转PDF）: {html_file} -> {pdf_path}")
                
                # 直接HTML转PDF
                success = html_to_pdf_direct(html_file, pdf_path)
                
                if success and os.path.exists(pdf_path):
                    task.pdf_file_path = pdf_path
                    logger.info(f"汇总报告PDF已生成（直接HTML转PDF）: {pdf_path}")
                else:
                    logger.warning("直接HTML转PDF失败，尝试使用Markdown转PDF方法")
                    # 回退到Markdown方法
                    raise Exception("HTML转PDF失败")
            else:
                logger.warning("HTML文件不存在，跳过自动PDF导出")
                
        except Exception as html_error:
            logger.warning(f"直接HTML转PDF失败: {str(html_error)}，尝试使用Markdown转PDF方法")
            
            # 回退到Markdown转PDF方法
            try:
                # 确保重新导入以获取最新状态
                import importlib
                import sys
                
                # 如果模块已经在sys.modules中，先移除它
                if 'utils.pdf_export' in sys.modules:
                    del sys.modules['utils.pdf_export']
                
                # 重新导入模块
                import utils.pdf_export
                importlib.reload(utils.pdf_export)
                from utils.pdf_export import export_report_to_pdf, PDF_EXPORT_AVAILABLE, MARKDOWN_AVAILABLE
                
                logger.info(f"PDF导出功能状态检查: MARKDOWN_AVAILABLE={MARKDOWN_AVAILABLE}, PDF_EXPORT_AVAILABLE={PDF_EXPORT_AVAILABLE}")
                
                if PDF_EXPORT_AVAILABLE:
                # 将HTML转换为Markdown（简单提取文本内容）
                import re
                from html.parser import HTMLParser
                
                class HTMLToText(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.text = []
                        self.skip_tags = {'script', 'style', 'head'}
                        self.in_skip = False
                    
                    def handle_starttag(self, tag, attrs):
                        if tag.lower() in self.skip_tags:
                            self.in_skip = True
                        elif tag.lower() == 'h1':
                            self.text.append('\n# ')
                        elif tag.lower() == 'h2':
                            self.text.append('\n## ')
                        elif tag.lower() == 'h3':
                            self.text.append('\n### ')
                        elif tag.lower() == 'p':
                            self.text.append('\n')
                        elif tag.lower() == 'br':
                            self.text.append('\n')
                    
                    def handle_endtag(self, tag):
                        if tag.lower() in self.skip_tags:
                            self.in_skip = False
                        elif tag.lower() in {'h1', 'h2', 'h3', 'p'}:
                            self.text.append('\n')
                    
                    def handle_data(self, data):
                        if not self.in_skip:
                            self.text.append(data.strip())
                
                parser = HTMLToText()
                parser.feed(html_report)
                markdown_content = ''.join(parser.text)
                
                # 清理多余的空白行
                markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
                
                # 导出PDF
                pdf_path = export_report_to_pdf(
                    report_content=markdown_content,
                    output_dir=report_agent.config.OUTPUT_DIR,
                    query=query,
                    engine_name="report"
                )
                
                if pdf_path:
                    task.pdf_file_path = pdf_path
                    logger.info(f"汇总报告PDF已生成: {pdf_path}")
                else:
                    logger.warning("PDF导出失败")
            else:
                logger.warning("PDF导出功能不可用")
        except Exception as e:
            logger.warning(f"自动导出PDF失败: {str(e)}")
        
        task.update_status("completed", 100)

    except Exception as e:
        logger.exception(f"报告生成过程中发生错误: {str(e)}")
        task.update_status("error", 0, str(e))
        # 只在出错时清理任务
        with task_lock:
            if current_task and current_task.task_id == task.task_id:
                current_task = None


@report_bp.route('/status', methods=['GET'])
def get_status():
    """获取Report Engine状态"""
    try:
        engines_status = check_engines_ready()

        return jsonify({
            'success': True,
            'initialized': report_agent is not None,
            'engines_ready': engines_status['ready'],
            'files_found': engines_status.get('files_found', []),
            'missing_files': engines_status.get('missing_files', []),
            'current_task': current_task.to_dict() if current_task else None
        })
    except Exception as e:
        logger.exception(f"获取Report Engine状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@report_bp.route('/generate', methods=['POST'])
def generate_report():
    """开始生成报告"""
    global current_task

    try:
        # 检查是否有任务在运行
        with task_lock:
            if current_task and current_task.status == "running":
                return jsonify({
                    'success': False,
                    'error': '已有报告生成任务在运行中',
                    'current_task': current_task.to_dict()
                }), 400

            # 如果有已完成的任务，清理它
            if current_task and current_task.status in ["completed", "error"]:
                current_task = None

        # 获取请求参数
        data = request.get_json() or {}
        query = data.get('query', '智能舆情分析报告')
        custom_template = data.get('custom_template', '')

        # 清空日志文件
        clear_report_log()

        # 检查Report Engine是否初始化
        if not report_agent:
            return jsonify({
                'success': False,
                'error': 'Report Engine未初始化'
            }), 500

        # 检查输入文件是否准备就绪（不重置基准，使用现有基准检测新文件）
        engines_status = check_engines_ready()
        if not engines_status['ready']:
            return jsonify({
                'success': False,
                'error': '输入文件未准备就绪',
                'missing_files': engines_status.get('missing_files', []),
                'baseline_counts': engines_status.get('baseline_counts', {}),
                'current_counts': engines_status.get('current_counts', {}),
                'new_files_found': engines_status.get('new_files_found', {})
            }), 400

        # 创建新任务
        task_id = f"report_{int(time.time())}"
        task = ReportTask(query, task_id, custom_template)

        with task_lock:
            current_task = task

        # 在后台线程中运行报告生成
        thread = threading.Thread(
            target=run_report_generation,
            args=(task, query, custom_template),
            daemon=True
        )
        thread.start()

        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '报告生成已启动',
            'task': task.to_dict()
        })

    except Exception as e:
        logger.exception(f"开始生成报告失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@report_bp.route('/progress/<task_id>', methods=['GET'])
def get_progress(task_id: str):
    """获取报告生成进度"""
    try:
        if not current_task or current_task.task_id != task_id:
            # 如果任务不存在，可能是已经完成并被清理了
            # 返回一个默认的完成状态而不是404
            return jsonify({
                'success': True,
                'task': {
                    'task_id': task_id,
                    'status': 'completed',
                    'progress': 100,
                    'error_message': '',
                    'has_result': True,
                    'report_file_ready': False,
                    'report_file_name': '',
                    'report_file_path': ''
                }
            })

        return jsonify({
            'success': True,
            'task': current_task.to_dict()
        })

    except Exception as e:
        logger.exception(f"获取报告生成进度失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@report_bp.route('/result/<task_id>', methods=['GET'])
def get_result(task_id: str):
    """获取报告生成结果"""
    try:
        if not current_task or current_task.task_id != task_id:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404

        if current_task.status != "completed":
            return jsonify({
                'success': False,
                'error': '报告尚未完成',
                'task': current_task.to_dict()
            }), 400

        return Response(
            current_task.html_content,
            mimetype='text/html'
        )

    except Exception as e:
        logger.exception(f"获取报告生成结果失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@report_bp.route('/export_pdf/<task_id>', methods=['POST'])
def export_pdf(task_id: str):
    """导出报告为PDF"""
    try:
        if not current_task or current_task.task_id != task_id:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404
        
        if current_task.status != "completed":
            return jsonify({
                'success': False,
                'error': '报告尚未完成',
                'task': current_task.to_dict()
            }), 400
        
        # 优先使用直接HTML转PDF（保持与浏览器完全一致的格式）
        try:
            from utils.pdf_export import html_to_pdf_direct
            
            # 如果报告已保存为HTML文件，直接使用HTML文件
            if current_task.report_file_path and os.path.exists(current_task.report_file_path):
                html_file = current_task.report_file_path
            else:
                # 如果没有保存的HTML文件，先保存HTML内容到临时文件
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                query_safe = "".join(c for c in current_task.query if c.isalnum() or c in (' ', '-', '_')).rstrip()[:30]
                if not query_safe:
                    query_safe = "report"
                
                html_file = os.path.join(report_agent.config.OUTPUT_DIR, f"temp_report_{query_safe}_{timestamp}.html")
                os.makedirs(os.path.dirname(html_file), exist_ok=True)
                
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(current_task.html_content)
                logger.info(f"临时HTML文件已保存: {html_file}")
            
            # 生成PDF文件名
            base_name = os.path.basename(html_file)
            pdf_filename = os.path.splitext(base_name)[0] + ".pdf"
            pdf_path = os.path.join(report_agent.config.OUTPUT_DIR, pdf_filename)
            pdf_path = os.path.abspath(pdf_path)
            
            logger.info(f"开始将HTML直接转换为PDF: {html_file} -> {pdf_path}")
            
            # 直接HTML转PDF
            success = html_to_pdf_direct(html_file, pdf_path)
            
            if success and os.path.exists(pdf_path):
                # 清理临时HTML文件（如果是临时文件）
                if html_file.startswith('temp_'):
                    try:
                        os.remove(html_file)
                        logger.info(f"临时HTML文件已删除: {html_file}")
                    except:
                        pass
                
                # 返回PDF文件
                return send_file(
                    pdf_path,
                    as_attachment=True,
                    download_name=os.path.basename(pdf_path),
                    mimetype='application/pdf'
                )
            else:
                logger.warning("直接HTML转PDF失败，尝试使用Markdown转PDF方法")
                # 如果直接HTML转PDF失败，回退到Markdown方法
                raise Exception("HTML转PDF失败，尝试Markdown方法")
                
        except Exception as e:
            logger.warning(f"直接HTML转PDF失败: {str(e)}，尝试使用Markdown转PDF方法")
            
            # 回退到Markdown转PDF方法
            try:
                import importlib
                import sys
                
                # 如果模块已经在sys.modules中，先移除它
                if 'utils.pdf_export' in sys.modules:
                    del sys.modules['utils.pdf_export']
                
                # 重新导入模块
                import utils.pdf_export
                importlib.reload(utils.pdf_export)
                from utils.pdf_export import export_report_to_pdf, PDF_EXPORT_AVAILABLE, MARKDOWN_AVAILABLE
                
                logger.info(f"PDF导出功能状态检查: MARKDOWN_AVAILABLE={MARKDOWN_AVAILABLE}, PDF_EXPORT_AVAILABLE={PDF_EXPORT_AVAILABLE}")
                
                if not PDF_EXPORT_AVAILABLE:
                    return jsonify({
                        'success': False,
                        'error': 'PDF导出功能不可用，请安装: pip install playwright 或 pip install markdown reportlab'
                    }), 400
                
                # 将HTML转换为Markdown
                import re
                from html.parser import HTMLParser
                
                class HTMLToText(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.text = []
                        self.skip_tags = {'script', 'style', 'head'}
                        self.in_skip = False
                    
                    def handle_starttag(self, tag, attrs):
                        if tag.lower() in self.skip_tags:
                            self.in_skip = True
                        elif tag.lower() == 'h1':
                            self.text.append('\n# ')
                        elif tag.lower() == 'h2':
                            self.text.append('\n## ')
                        elif tag.lower() == 'h3':
                            self.text.append('\n### ')
                        elif tag.lower() == 'p':
                            self.text.append('\n')
                        elif tag.lower() == 'br':
                            self.text.append('\n')
                    
                    def handle_endtag(self, tag):
                        if tag.lower() in self.skip_tags:
                            self.in_skip = False
                        elif tag.lower() in {'h1', 'h2', 'h3', 'p'}:
                            self.text.append('\n')
                    
                    def handle_data(self, data):
                        if not self.in_skip:
                            self.text.append(data.strip())
                
                parser = HTMLToText()
                parser.feed(current_task.html_content)
                markdown_content = ''.join(parser.text)
                
                # 清理多余的空白行
                markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
                
                # 导出PDF
                pdf_path = export_report_to_pdf(
                    report_content=markdown_content,
                    output_dir=report_agent.config.OUTPUT_DIR,
                    query=current_task.query,
                    engine_name="report"
                )
                
                if pdf_path and os.path.exists(pdf_path):
                    # 返回PDF文件
                    return send_file(
                        pdf_path,
                        as_attachment=True,
                        download_name=os.path.basename(pdf_path),
                        mimetype='application/pdf'
                    )
                else:
                    return jsonify({
                        'success': False,
                        'error': 'PDF生成失败'
                    }), 500
            except Exception as markdown_error:
                logger.exception(f"Markdown转PDF也失败: {str(markdown_error)}")
                return jsonify({
                    'success': False,
                    'error': f'PDF导出失败: {str(markdown_error)}'
                }), 500
                
        except ImportError as e:
            logger.exception(f"PDF导出功能导入失败: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'PDF导出功能不可用: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.exception(f"导出PDF失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@report_bp.route('/result/<task_id>/json', methods=['GET'])
def get_result_json(task_id: str):
    """获取报告生成结果（JSON格式）"""
    try:
        if not current_task or current_task.task_id != task_id:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404

        if current_task.status != "completed":
            return jsonify({
                'success': False,
                'error': '报告尚未完成',
                'task': current_task.to_dict()
            }), 400

        return jsonify({
            'success': True,
            'task': current_task.to_dict(),
            'html_content': current_task.html_content
        })

    except Exception as e:
        logger.exception(f"获取报告生成结果失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@report_bp.route('/download/<task_id>', methods=['GET'])
def download_report(task_id: str):
    """下载已生成的报告HTML文件"""
    try:
        if not current_task or current_task.task_id != task_id:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404

        if current_task.status != "completed" or not current_task.report_file_path:
            return jsonify({
                'success': False,
                'error': '报告尚未完成或尚未保存'
            }), 400

        if not os.path.exists(current_task.report_file_path):
            return jsonify({
                'success': False,
                'error': '报告文件不存在或已被删除'
            }), 404

        download_name = current_task.report_file_name or os.path.basename(current_task.report_file_path)
        return send_file(
            current_task.report_file_path,
            mimetype='text/html',
            as_attachment=True,
            download_name=download_name
        )

    except Exception as e:
        logger.exception(f"下载报告失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@report_bp.route('/cancel/<task_id>', methods=['POST'])
def cancel_task(task_id: str):
    """取消报告生成任务"""
    global current_task

    try:
        with task_lock:
            if current_task and current_task.task_id == task_id:
                if current_task.status == "running":
                    current_task.update_status("cancelled", 0, "用户取消任务")
                current_task = None

                return jsonify({
                    'success': True,
                    'message': '任务已取消'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '任务不存在或无法取消'
                }), 404

    except Exception as e:
        logger.exception(f"取消报告生成任务失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@report_bp.route('/templates', methods=['GET'])
def get_templates():
    """获取可用模板列表"""
    try:
        if not report_agent:
            return jsonify({
                'success': False,
                'error': 'Report Engine未初始化'
            }), 500

        template_dir = settings.TEMPLATE_DIR
        templates = []

        if os.path.exists(template_dir):
            for filename in os.listdir(template_dir):
                if filename.endswith('.md'):
                    template_path = os.path.join(template_dir, filename)
                    try:
                        with open(template_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        templates.append({
                            'name': filename.replace('.md', ''),
                            'filename': filename,
                            'description': content.split('\n')[0] if content else '无描述',
                            'size': len(content)
                        })
                    except Exception as e:
                        logger.exception(f"读取模板失败 {filename}: {str(e)}")

        return jsonify({
            'success': True,
            'templates': templates,
            'template_dir': template_dir
        })

    except Exception as e:
        logger.exception(f"获取可用模板列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# 错误处理
@report_bp.errorhandler(404)
def not_found(error):
    logger.exception(f"API端点不存在: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'API端点不存在'
    }), 404


@report_bp.errorhandler(500)
def internal_error(error):
    logger.exception(f"服务器内部错误: {str(error)}")
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500


def clear_report_log():
    """清空report.log文件"""
    try:
        log_file = settings.LOG_FILE
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('')
        logger.info(f"已清空日志文件: {log_file}")
    except Exception as e:
        logger.exception(f"清空日志文件失败: {str(e)}")


@report_bp.route('/log', methods=['GET'])
def get_report_log():
    """获取report.log内容"""
    try:
        log_file = settings.LOG_FILE
        
        if not os.path.exists(log_file):
            return jsonify({
                'success': True,
                'log_lines': []
            })
        
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 清理行尾的换行符
        log_lines = [line.rstrip('\n\r') for line in lines if line.strip()]
        
        return jsonify({
            'success': True,
            'log_lines': log_lines
        })
        
    except Exception as e:
        logger.exception(f"读取日志失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'读取日志失败: {str(e)}'
        }), 500


@report_bp.route('/log/clear', methods=['POST'])
def clear_log():
    """手动清空日志"""
    try:
        clear_report_log()
        return jsonify({
            'success': True,
            'message': '日志已清空'
        })
    except Exception as e:
        logger.exception(f"清空日志失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'清空日志失败: {str(e)}'
        }), 500


@report_bp.route('/reset_baseline', methods=['POST'])
def reset_baseline_api():
    """重置文件数量基准（在开始新搜索时调用）"""
    try:
        if not report_agent:
            return jsonify({
                'success': False,
                'error': 'Report Engine未初始化'
            }), 500
        
        directories = {
            'market': 'market_engine_streamlit_reports',
            'customer': 'customer_engine_streamlit_reports',
            'compete': 'compete_engine_streamlit_reports'
        }
        
        # 重置基准
        report_agent.file_baseline.reset_baseline(directories)
        
        logger.info("文件数量基准已重置，准备检测新文件")
        
        return jsonify({
            'success': True,
            'message': '文件数量基准已重置',
            'baseline': report_agent.file_baseline.baseline_data
        })
    except Exception as e:
        logger.exception(f"重置基准失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'重置基准失败: {str(e)}'
        }), 500