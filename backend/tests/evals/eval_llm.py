import os
import logging
from typing import Optional, Any
from deepeval.models.base_model import DeepEvalBaseLLM
from langchain_core.messages import HumanMessage
from backend.agent.llm_factory import get_llm

logger = logging.getLogger(__name__)


class DeepEvalCustomModel(DeepEvalBaseLLM):
    """
    Custom DeepEval evaluator model leveraging existing Gemini Flash or DeepSeek API credentials.
    Eliminates any requirement for OpenAI API keys.
    """
    def __init__(self, provider: str = "gemini", model_name: Optional[str] = None):
        self.provider = provider
        self.chosen_model = model_name or ("gemini-2.5-flash" if provider == "gemini" else "deepseek-chat")
        super().__init__(model=self.chosen_model)

    def load_model(self) -> Any:
        return get_llm(provider=self.provider, temperature=0.0, with_fallback=True)

    def get_model_name(self) -> str:
        return f"{self.provider}:{self.chosen_model}"

    def generate(self, prompt: str, schema=None, **kwargs) -> str:
        if schema:
            schema_str = schema.model_json_schema() if hasattr(schema, "model_json_schema") else str(schema)
            prompt = f"{prompt}\n\nSTRICT INSTRUCTION: Output valid JSON adhering to this schema:\n{schema_str}"
        response = self.model.invoke([HumanMessage(content=prompt)])
        content = response.content if hasattr(response, "content") else str(response)
        return content

    async def a_generate(self, prompt: str, schema=None, **kwargs) -> str:
        if schema:
            schema_str = schema.model_json_schema() if hasattr(schema, "model_json_schema") else str(schema)
            prompt = f"{prompt}\n\nSTRICT INSTRUCTION: Output valid JSON adhering to this schema:\n{schema_str}"
        response = await self.model.ainvoke([HumanMessage(content=prompt)])
        content = response.content if hasattr(response, "content") else str(response)
        return content

