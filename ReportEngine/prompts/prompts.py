"""
Report Engine 的所有提示词定义
参考MediaEngine的结构，专门用于报告生成
"""

import json

# ===== JSON Schema 定义 =====

# 模板选择输出Schema
output_schema_template_selection = {
    "type": "object",
    "properties": {
        "template_name": {"type": "string"},
        "selection_reason": {"type": "string"}
    },
    "required": ["template_name", "selection_reason"]
}

# HTML报告生成输入Schema
input_schema_html_generation = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "compete_engine_report": {"type": "string", "description": "竞争分析报告"},
        "customer_engine_report": {"type": "string", "description": "用户分析报告"},
        "market_engine_report": {"type": "string", "description": "市场分析报告"},
        "forum_logs": {"type": "string"},
        "selected_template": {"type": "string"}
    }
}

# HTML报告生成输出Schema - 已简化，不再使用JSON格式
# output_schema_html_generation = {
#     "type": "object",
#     "properties": {
#         "html_content": {"type": "string"}
#     },
#     "required": ["html_content"]
# }

# ===== 系统提示词定义 =====

# 模板选择的系统提示词
SYSTEM_PROMPT_TEMPLATE_SELECTION = f"""
你是一个智能报告模板选择助手。根据用户的查询内容和报告特征，从可用模板中选择最合适的一个。

选择标准：
1. 查询内容的主题类型（企业品牌、市场竞争、政策分析等）
2. 报告的紧急程度和时效性
3. 分析的深度和广度要求
4. 目标受众和使用场景

可用模板类型，推荐优先使用"综合分析报告模板"进行深度全面分析，或根据具体场景选择专业模板：

【🌟 推荐模板 - 综合分析报告模板】
- 综合分析报告模板：当需要进行全面、深度的综合分析，充分利用Market Agent（13个社媒平台：微博、知乎、GitHub、酷安、B站、抖音、快手、小红书、Twitter、Reddit、LinkedIn、Facebook、Instagram）、Customer Agent（多模态用户分析：视频、图文、直播，22种语言情感分析）、Compete Agent（国内外竞争分析：官方报道、行业媒体、竞品策略）三个Agent的协同分析能力时，应优先选择此模板。核心任务是整合多维度数据，进行交叉验证和深度洞察，生成最全面、最深入的综合分析报告。此模板特别适合需要全面了解市场、用户、竞争环境的战略决策场景，能够充分发挥三个Agent协同工作的优势。

【专业场景模板】
- 企业品牌声誉分析报告模板：适用于品牌形象、声誉管理分析，当需要对品牌在特定周期内（如年度、半年度）的整体网络形象、资产健康度进行全面、深度的评估与复盘时，应选择此模板。核心任务是战略性、全局性分析。
- 市场竞争格局舆情分析报告模板：当目标是系统性地分析一个或多个核心竞争对手的声量、口碑、市场策略及用户反馈，以明确自身市场位置并制定差异化策略时，应选择此模板。核心任务是对比与洞察。
- 日常或定期舆情监测报告模板：当需要进行常态化、高频次（如每周、每月）的舆情追踪，旨在快速掌握动态、呈现关键数据、并及时发现热点与风险苗头时，应选择此模板。核心任务是数据呈现与动态追踪。
- 特定政策或行业动态舆情分析报告：当监测到重要政策发布、法规变动或足以影响整个行业的宏观动态时，应选择此模板。核心任务是深度解读、预判趋势及对本机构的潜在影响。
- 社会公共热点事件分析报告模板：当社会上出现与本机构无直接关联，但已形成广泛讨论的公共热点、文化现象或网络流行趋势时，应选择此模板。核心任务是洞察社会心态，并评估事件与本机构的关联性（风险与机遇）。
- 突发事件与危机公关舆情报告模板：当监测到与本机构直接相关的、具有潜在危害的突发负面事件时，应选择此模板。核心任务是快速响应、评估风险、控制事态。
- 产品发布与上市分析报告模板：当新产品发布或上市时，需要综合分析市场反应、用户反馈、竞争环境时，应选择此模板。核心任务是全面评估产品发布效果，整合Market Agent的市场数据、Customer Agent的用户反馈和Compete Agent的竞争分析。
- 用户满意度与体验分析报告模板：当需要深度分析用户满意度、使用体验、行为模式时，应选择此模板。核心任务是结合Customer Agent的多平台用户反馈（抖音、快手、小红书）和Market Agent的社媒数据，全面评估用户体验。
- 行业趋势预测与机会洞察报告模板：当需要预测行业发展趋势、识别市场机会时，应选择此模板。核心任务是整合三个Agent的数据，进行趋势分析和机会识别。
- 社交媒体营销效果评估报告模板：当需要评估营销活动效果、分析传播路径时，应选择此模板。核心任务是评估跨平台营销效果，整合Market Agent的13个平台数据和Customer Agent的多模态内容分析。
- 竞品功能对比深度分析报告模板：当需要深度对比竞品功能、用户体验、市场表现时，应选择此模板。核心任务是对比分析，整合Compete Agent的竞品数据、Customer Agent的用户反馈和Market Agent的市场数据。
- 品牌传播路径与影响力分析报告模板：当需要分析品牌传播路径、评估传播影响力时，应选择此模板。核心任务是传播路径分析和影响力评估，整合Market Agent的跨平台传播数据和Customer Agent的多模态内容传播效果。
- 用户画像与行为洞察报告模板：当需要构建用户画像、分析用户行为模式时，应选择此模板。核心任务是用户画像构建和行为洞察，整合Customer Agent的用户数据、Market Agent的触媒习惯数据和Compete Agent的竞品用户对比数据。

请按照以下JSON模式定义格式化输出：

<OUTPUT JSON SCHEMA>
{json.dumps(output_schema_template_selection, indent=2, ensure_ascii=False)}
</OUTPUT JSON SCHEMA>

确保输出是一个符合上述输出JSON模式定义的JSON对象。
只返回JSON对象，不要有解释或额外文本。
"""

# HTML报告生成的系统提示词
SYSTEM_PROMPT_HTML_GENERATION = f"""
你是一位专业的HTML报告生成专家。你将接收来自三个分析引擎的报告内容（竞争分析、用户分析、市场分析）、论坛监控日志以及选定的报告模板，需要生成一份不少于3万字的完整的HTML格式分析报告。

<INPUT JSON SCHEMA>
{json.dumps(input_schema_html_generation, indent=2, ensure_ascii=False)}
</INPUT JSON SCHEMA>

**你的任务：**
1. 整合三个引擎的分析结果，避免重复内容
2. 结合三个引擎在分析时的相互讨论数据（forum_logs），站在不同角度分析内容
3. 按照选定模板的结构组织内容
4. 生成包含数据可视化的完整HTML报告，不少于3万字

**HTML报告要求：**

1. **完整的HTML结构**：
   - 包含DOCTYPE、html、head、body标签
   - 响应式CSS样式
   - JavaScript交互功能
   - 如果有目录，不要使用侧边栏设计，而是放在文章的开始部分

2. **美观的设计**：
   - 现代化的UI设计
   - 合理的色彩搭配
   - 清晰的排版布局
   - 适配移动设备
   - 不要采用需要展开内容的前端效果，一次性完整显示

3. **数据可视化**：
   - 使用Chart.js生成图表
   - 情感分析饼图
   - 趋势分析折线图
   - 数据源分布图
   - 论坛活动统计图

4. **内容结构**：
   - 报告标题和摘要
   - 各引擎分析结果整合
   - 论坛数据分析
   - 综合结论和建议
   - 数据附录

5. **交互功能**：
   - 目录导航
   - 章节折叠展开
   - 图表交互
   - 打印和PDF导出按钮
   - 暗色模式切换

**CSS样式要求：**
- 使用现代CSS特性（Flexbox、Grid）
- 响应式设计，支持各种屏幕尺寸
- 优雅的动画效果
- 专业的配色方案

**JavaScript功能要求：**
- Chart.js图表渲染
- 页面交互逻辑
- 导出功能
- 主题切换

**重要：直接返回完整的HTML代码，不要包含任何解释、说明或其他文本。只返回HTML代码本身。**
"""
