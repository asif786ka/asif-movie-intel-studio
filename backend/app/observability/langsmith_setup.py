import os
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def setup_langsmith():
    if not settings.langsmith_tracing_enabled:
        logger.info("LangSmith tracing disabled")
        return

    if not settings.langsmith_api_key:
        logger.warning("LangSmith API key not set, tracing disabled")
        return

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project

    logger.info(f"LangSmith tracing enabled for project: {settings.langsmith_project}")
