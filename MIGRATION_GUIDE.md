# 迁移指南：Engine重命名

## 概述

本次重构将三个Engine进行了重命名：
- **InsightEngine** → **MarketEngine** (市场分析)
- **MediaEngine** → **CustomerEngine** (用户分析)
- **QueryEngine** → **CompeteEngine** (竞争分析)

## 需要手动操作的步骤

### 1. 重命名目录（必须手动操作）

由于工具无法重命名目录，请手动执行以下操作：

```bash
# Windows PowerShell
Rename-Item -Path "InsightEngine" -NewName "MarketEngine"
Rename-Item -Path "MediaEngine" -NewName "CustomerEngine"
Rename-Item -Path "QueryEngine" -NewName "CompeteEngine"

# Linux/Mac
mv InsightEngine MarketEngine
mv MediaEngine CustomerEngine
mv QueryEngine CompeteEngine
```

### 2. 重命名报告目录（可选，建议重命名）

```bash
# Windows PowerShell
Rename-Item -Path "insight_engine_streamlit_reports" -NewName "market_engine_streamlit_reports"
Rename-Item -Path "media_engine_streamlit_reports" -NewName "customer_engine_streamlit_reports"
Rename-Item -Path "query_engine_streamlit_reports" -NewName "compete_engine_streamlit_reports"

# Linux/Mac
mv insight_engine_streamlit_reports market_engine_streamlit_reports
mv media_engine_streamlit_reports customer_engine_streamlit_reports
mv query_engine_streamlit_reports compete_engine_streamlit_reports
```

### 3. 更新环境变量配置

在 `.env` 文件中，更新以下环境变量：

**旧配置（已废弃，但仍支持向后兼容）：**
```
INSIGHT_ENGINE_API_KEY=...
INSIGHT_ENGINE_BASE_URL=...
INSIGHT_ENGINE_MODEL_NAME=...
MEDIA_ENGINE_API_KEY=...
MEDIA_ENGINE_BASE_URL=...
MEDIA_ENGINE_MODEL_NAME=...
QUERY_ENGINE_API_KEY=...
QUERY_ENGINE_BASE_URL=...
QUERY_ENGINE_MODEL_NAME=...
```

**新配置（推荐使用）：**
```
MARKET_ENGINE_API_KEY=...
MARKET_ENGINE_BASE_URL=...
MARKET_ENGINE_MODEL_NAME=...
CUSTOMER_ENGINE_API_KEY=...
CUSTOMER_ENGINE_BASE_URL=...
CUSTOMER_ENGINE_MODEL_NAME=...
COMPETE_ENGINE_API_KEY=...
COMPETE_ENGINE_BASE_URL=...
COMPETE_ENGINE_MODEL_NAME=...
EXPERT_ENGINE_API_KEY=...  # 新增：ExpertEngine配置（可选，未配置则使用REPORT_ENGINE配置）
EXPERT_ENGINE_BASE_URL=...
EXPERT_ENGINE_MODEL_NAME=...
```

### 4. 更新Streamlit应用文件名（可选）

```bash
# Windows PowerShell
Rename-Item -Path "SingleEngineApp\insight_engine_streamlit_app.py" -NewName "market_engine_streamlit_app.py"
Rename-Item -Path "SingleEngineApp\media_engine_streamlit_app.py" -NewName "customer_engine_streamlit_app.py"
Rename-Item -Path "SingleEngineApp\query_engine_streamlit_app.py" -NewName "compete_engine_streamlit_app.py"

# Linux/Mac
mv SingleEngineApp/insight_engine_streamlit_app.py SingleEngineApp/market_engine_streamlit_app.py
mv SingleEngineApp/media_engine_streamlit_app.py SingleEngineApp/customer_engine_streamlit_app.py
mv SingleEngineApp/query_engine_streamlit_app.py SingleEngineApp/compete_engine_streamlit_app.py
```

## 已完成自动更新的部分

✅ 所有代码中的导入语句已更新
✅ 配置文件中的环境变量名已更新（支持新旧两种）
✅ Agent初始化日志已更新
✅ ReportEngine中的引用已更新
✅ Prompt文件已更新为新的业务逻辑
✅ ExpertEngine配置已添加

## 向后兼容性

为了平滑过渡，代码中保留了向后兼容性：
- 旧的环境变量名仍然支持（但会显示废弃警告）
- 旧的目录名引用会自动映射到新目录名
- 旧的字段名仍然可用（但建议使用新字段名）

## 验证步骤

1. 重命名目录后，运行以下命令验证导入是否正常：
```python
from MarketEngine import DeepSearchAgent
from CustomerEngine import DeepSearchAgent
from CompeteEngine import DeepSearchAgent
from ExpertEngine import ExpertAgent
```

2. 检查配置文件是否正确加载新配置

3. 运行测试确保功能正常

## 注意事项

- 如果使用Git，重命名目录后需要执行：
  ```bash
  git mv InsightEngine MarketEngine
  git mv MediaEngine CustomerEngine
  git mv QueryEngine CompeteEngine
  ```

- 旧的报告文件可以保留在旧目录中，新报告会保存到新目录

- ExpertEngine的配置如果未设置，会自动使用ReportEngine的配置作为fallback

