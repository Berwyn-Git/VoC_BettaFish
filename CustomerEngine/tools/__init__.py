"""
工具调用模块
提供外部工具接口，如多模态搜索等
"""

from .search import (
    BochaMultimodalSearch,
    WebpageResult,
    ImageResult,
    ModalCardResult,
    BochaResponse,
    print_response_summary
)

# 导入通用情感分析工具（从MarketEngine导入）
try:
    from MarketEngine.tools import (
        WeiboMultilingualSentimentAnalyzer,
        SentimentResult,
        BatchSentimentResult,
        multilingual_sentiment_analyzer,
        analyze_sentiment
    )
    SENTIMENT_ANALYZER_AVAILABLE = True
except ImportError:
    # 如果MarketEngine不可用，则设置为None
    WeiboMultilingualSentimentAnalyzer = None
    SentimentResult = None
    BatchSentimentResult = None
    multilingual_sentiment_analyzer = None
    analyze_sentiment = None
    SENTIMENT_ANALYZER_AVAILABLE = False

__all__ = [
    "BochaMultimodalSearch",
    "WebpageResult", 
    "ImageResult",
    "ModalCardResult",
    "BochaResponse",
    "print_response_summary",
    "WeiboMultilingualSentimentAnalyzer",
    "SentimentResult",
    "BatchSentimentResult",
    "multilingual_sentiment_analyzer",
    "analyze_sentiment",
    "SENTIMENT_ANALYZER_AVAILABLE"
]
