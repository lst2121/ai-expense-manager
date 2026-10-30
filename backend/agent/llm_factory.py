import os
import logging
from typing import Optional, Any
from dotenv import load_dotenv

load_dotenv()

# Disable LangSmith tracing unless explicitly valid
if os.getenv("LANGSMITH_TRACING", "false").lower() != "true":
    os.environ["LANGSMITH_TRACING"] = "false"

logger = logging.getLogger(__name__)


def get_gemini_llm(model: Optional[str] = None, temperature: float = 0.0) -> Any:
    """Instantiate Google Gemini LLM via langchain-google-genai."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    model_name = model or os.getenv("GEMINI_MODEL", "gemini-flash-latest")

    return ChatGoogleGenerativeAI(
        model=model_name,
        api_key=api_key,
        temperature=temperature,
        timeout=25,
        max_retries=2,
    )


def get_deepseek_llm(model: Optional[str] = None, temperature: float = 0.0) -> Any:
    """Instantiate DeepSeek LLM via langchain-deepseek."""
    from langchain_deepseek import ChatDeepSeek

    api_key = os.getenv("DEEPSEEK_API_KEY")
    api_base = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model_name = model or os.getenv("DEEPSEEK_MODEL", "deepseek-flash")

    return ChatDeepSeek(
        model=model_name,
        api_key=api_key,
        api_base=api_base,
        temperature=temperature,
        timeout=25,
        max_retries=2,
    )


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.0,
    with_fallback: bool = True
) -> Any:
    """
    Factory creating the configured LLM.
    Default: Gemini (gemini-flash-latest) -> Fallback: DeepSeek
    """
    chosen_provider = (provider or os.getenv("DEFAULT_LLM_PROVIDER", "gemini")).lower()

    if chosen_provider == "deepseek":
        primary = get_deepseek_llm(model=model, temperature=temperature)
        if with_fallback:
            try:
                fallback = get_gemini_llm(temperature=temperature)
                return primary.with_fallbacks([fallback])
            except Exception as e:
                logger.warning(f"Could not configure Gemini fallback: {e}")
        return primary
    else:
        # Default: Gemini
        primary = get_gemini_llm(model=model, temperature=temperature)
        if with_fallback:
            try:
                fallback = get_deepseek_llm(temperature=temperature)
                return primary.with_fallbacks([fallback])
            except Exception as e:
                logger.warning(f"Could not configure DeepSeek fallback: {e}")
        return primary
