"""
Streamlit Web界面
为Customer Agent（用户分析）提供友好的Web界面
"""

import os
import sys
import streamlit as st
from datetime import datetime
import json
import locale
from loguru import logger

# 设置UTF-8编码环境
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# 设置系统编码
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except locale.Error:
        pass

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from CustomerEngine import DeepSearchAgent, Settings
from config import settings
from utils.github_issues import error_with_issue_link


def main():
    """主函数"""
    st.set_page_config(
        page_title="用户分析Agent",
        page_icon="",
        layout="wide"
    )

    st.title("用户分析Agent")
    st.markdown("专业的用户分析AI代理")
    st.markdown("突破传统文本交流限制，广泛的浏览抖音、快手、小红书的视频、图文、直播，深度分析用户行为和用户反馈")
    st.markdown("使用现代化搜索引擎提供的诸如日历卡、天气卡、股票卡等多模态结构化信息进一步增强能力")

    # 检查URL参数
    try:
        # 尝试使用新版本的query_params
        query_params = st.query_params
        auto_query = query_params.get('query', '')
        auto_search = query_params.get('auto_search', 'false').lower() == 'true'
    except AttributeError:
        # 兼容旧版本
        query_params = st.experimental_get_query_params()
        auto_query = query_params.get('query', [''])[0]
        auto_search = query_params.get('auto_search', ['false'])[0].lower() == 'true'

    # ----- 配置被硬编码 -----
    # 强制使用 Gemini
    # 优先使用新配置，兼容旧配置
    model_name = (settings.CUSTOMER_ENGINE_MODEL_NAME or settings.MEDIA_ENGINE_MODEL_NAME or "gemini-2.5-pro")
    # 默认高级配置
    max_reflections = 2
    max_content_length = 20000

    # 简化的研究查询展示区域

    # 如果有自动查询，使用它作为默认值，否则显示占位符
    display_query = auto_query if auto_query else "等待从主页面接收分析内容..."

    # 只读的查询展示区域
    st.text_area(
        "当前查询",
        value=display_query,
        height=100,
        disabled=True,
        help="查询内容由主页面的搜索框控制",
        label_visibility="hidden"
    )

    # 自动搜索逻辑
    start_research = False
    query = auto_query

    if auto_search and auto_query and 'auto_search_executed' not in st.session_state:
        st.session_state.auto_search_executed = True
        start_research = True
    elif auto_query and not auto_search:
        st.warning("等待搜索启动信号...")

    # 验证配置
    if start_research:
        if not query.strip():
            st.error("请输入研究查询")
            logger.error("请输入研究查询")
            return

        # 检查API密钥（优先使用新配置，兼容旧配置）
        engine_key = settings.CUSTOMER_ENGINE_API_KEY or settings.MEDIA_ENGINE_API_KEY
        if not engine_key:
            st.error("请在您的环境变量中设置CUSTOMER_ENGINE_API_KEY或MEDIA_ENGINE_API_KEY")
            logger.error("请在您的环境变量中设置CUSTOMER_ENGINE_API_KEY或MEDIA_ENGINE_API_KEY")
            return
        if not settings.BOCHA_WEB_SEARCH_API_KEY:
            st.error("请在您的环境变量中设置BOCHA_WEB_SEARCH_API_KEY")
            logger.error("请在您的环境变量中设置BOCHA_WEB_SEARCH_API_KEY")
            return

        # 自动使用配置文件中的API密钥
        bocha_key = settings.BOCHA_WEB_SEARCH_API_KEY

        # 构建 Settings（pydantic_settings风格，优先大写环境变量）
        config = Settings(
            CUSTOMER_ENGINE_API_KEY=engine_key or settings.CUSTOMER_ENGINE_API_KEY,  # 优先使用新配置
            CUSTOMER_ENGINE_BASE_URL=settings.CUSTOMER_ENGINE_BASE_URL or settings.MEDIA_ENGINE_BASE_URL,
            CUSTOMER_ENGINE_MODEL_NAME=model_name or settings.CUSTOMER_ENGINE_MODEL_NAME or settings.MEDIA_ENGINE_MODEL_NAME,
            MEDIA_ENGINE_API_KEY=engine_key,  # 兼容旧配置
            MEDIA_ENGINE_BASE_URL=settings.MEDIA_ENGINE_BASE_URL,
            MEDIA_ENGINE_MODEL_NAME=model_name,
            BOCHA_WEB_SEARCH_API_KEY=bocha_key,
            MAX_REFLECTIONS=max_reflections,
            SEARCH_CONTENT_MAX_LENGTH=max_content_length,
            OUTPUT_DIR="customer_engine_streamlit_reports",  # 用户分析（原media）
        )

        # 执行研究
        execute_research(query, config)


def execute_research(query: str, config: Settings):
    """执行研究"""
    try:
        # 创建进度条
        progress_bar = st.progress(0)
        status_text = st.empty()

        # 初始化Agent
        status_text.text("正在初始化Agent...")
        agent = DeepSearchAgent(config)
        st.session_state.agent = agent

        progress_bar.progress(10)

        # 生成报告结构
        status_text.text("正在生成报告结构...")
        agent._generate_report_structure(query)
        progress_bar.progress(20)

        # 处理段落
        total_paragraphs = len(agent.state.paragraphs)
        for i in range(total_paragraphs):
            status_text.text(f"正在处理段落 {i + 1}/{total_paragraphs}: {agent.state.paragraphs[i].title}")

            # 初始搜索和总结
            agent._initial_search_and_summary(i)
            progress_value = 20 + (i + 0.5) / total_paragraphs * 60
            progress_bar.progress(int(progress_value))

            # 反思循环
            agent._reflection_loop(i)
            agent.state.paragraphs[i].research.mark_completed()

            progress_value = 20 + (i + 1) / total_paragraphs * 60
            progress_bar.progress(int(progress_value))

        # 生成最终报告
        status_text.text("正在生成最终报告...")
        logger.info("正在生成最终报告...")
        final_report = agent._generate_final_report()
        progress_bar.progress(90)

        # 保存报告
        status_text.text("正在保存报告...")
        logger.info("正在保存报告...")
        agent._save_report(final_report)
        progress_bar.progress(100)

        status_text.text("研究完成！")
        logger.info("研究完成！")
        # 显示结果
        display_results(agent, final_report)

    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        error_display = error_with_issue_link(
            f"研究过程中发生错误: {str(e)}",
            error_traceback,
            app_name="Media Engine Streamlit App"
        )
        st.error(error_display)
        logger.exception(f"研究过程中发生错误: {str(e)}")


def display_results(agent: DeepSearchAgent, final_report: str):
    """显示研究结果"""
    st.header("研究结果")

    # 导出PDF按钮
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("📄 导出PDF", type="primary", use_container_width=True):
            try:
                from utils.pdf_export import export_report_to_pdf, PDF_EXPORT_AVAILABLE
                
                if not PDF_EXPORT_AVAILABLE:
                    st.error("PDF导出功能不可用，请安装: pip install markdown weasyprint")
                else:
                    with st.spinner("正在生成PDF..."):
                        pdf_path = export_report_to_pdf(
                            report_content=final_report,
                            output_dir=agent.config.OUTPUT_DIR,
                            query=agent.state.query,
                            engine_name="customer"
                        )
                        
                        if pdf_path:
                            # 读取PDF文件并提供下载
                            with open(pdf_path, 'rb') as pdf_file:
                                st.download_button(
                                    label="📥 下载PDF",
                                    data=pdf_file.read(),
                                    file_name=os.path.basename(pdf_path),
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                            st.success(f"PDF已生成: {os.path.basename(pdf_path)}")
                        else:
                            st.error("PDF生成失败，请查看日志")
            except Exception as e:
                st.error(f"导出PDF时出错: {str(e)}")
                logger.exception(f"导出PDF失败: {str(e)}")

    # 结果标签页（已移除下载选项）
    tab1, tab2 = st.tabs(["研究小结", "引用信息"])

    with tab1:
        st.markdown(final_report)

    with tab2:
        # 段落详情
        st.subheader("段落详情")
        for i, paragraph in enumerate(agent.state.paragraphs):
            with st.expander(f"段落 {i + 1}: {paragraph.title}"):
                st.write("**预期内容:**", paragraph.content)
                st.write("**最终内容:**", paragraph.research.latest_summary[:300] + "..."
                if len(paragraph.research.latest_summary) > 300
                else paragraph.research.latest_summary)
                st.write("**搜索次数:**", paragraph.research.get_search_count())
                st.write("**反思次数:**", paragraph.research.reflection_iteration)

        # 搜索历史
        st.subheader("搜索历史")
        all_searches = []
        for paragraph in agent.state.paragraphs:
            all_searches.extend(paragraph.research.search_history)

        if all_searches:
            for i, search in enumerate(all_searches):
                with st.expander(f"搜索 {i + 1}: {search.query}"):
                    st.write("**URL:**", search.url)
                    st.write("**标题:**", search.title)
                    st.write("**内容预览:**",
                             search.content[:200] + "..." if len(search.content) > 200 else search.content)
                    if search.score:
                        st.write("**相关度评分:**", search.score)


if __name__ == "__main__":
    main()
