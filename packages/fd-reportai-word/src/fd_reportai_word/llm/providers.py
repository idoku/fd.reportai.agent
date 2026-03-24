from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage

from .config import build_common_kwargs, env_float, env_int, env_str, load_dotenv_if_available
from .registry import GLOBAL_LLM_REGISTRY
from .types import LlmProviderConfig, SupportsInvoke

load_dotenv_if_available()


class EchoChatModel:
    def __init__(self, model: str = "mock-echo") -> None:
        self.model = model

    def invoke(self, input: Any, config: Any = None, **kwargs: Any) -> AIMessage:
        text = self._stringify_input(input)
        if "必须输出的字段" in text and "输入数据(JSON)" in text:
            payload = self._extract_selected_input(text)
            content = json.dumps(self._build_cover_fields(payload), ensure_ascii=False)
            return AIMessage(content=content, response_metadata={"model_name": self.model})
        return AIMessage(
            content=(
                "[MOCK:langchain]\n"
                "该内容由 LangChain mock provider 生成。接入真实模型后这里会变成正式输出。\n\n"
                f"{text[:400]}"
            ),
            response_metadata={"model_name": self.model},
        )

    def _stringify_input(self, input: Any) -> str:
        if isinstance(input, list):
            return "\n".join(str(getattr(item, "content", item)) for item in input)
        return str(input)

    def _extract_selected_input(self, text: str) -> dict[str, Any]:
        marker = "```json"
        if marker not in text:
            return {}
        content = text.split(marker, 1)[1].split("```", 1)[0].strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {}

    def _build_cover_fields(self, payload: dict[str, Any]) -> dict[str, str]:
        info = payload.get("项目信息", {})
        return {
            "报告标题": str(info.get("报告标题", "土地估价报告")),
            "项目名称": str(info.get("项目名称", "")),
            "委托方": str(info.get("委托方", "")),
            "报告编号": str(info.get("报告编号", "")),
            "提交日期": str(info.get("提交日期", "")),
        }


def _build_chat_openai(config: LlmProviderConfig) -> SupportsInvoke:
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise RuntimeError(
            "langchain-openai is not installed. Install it before using OpenAI-compatible providers."
        ) from exc

    kwargs = {
        "model": config.model,
        "temperature": config.temperature,
        **build_common_kwargs(dict(config.extra)),
    }
    if config.api_key:
        kwargs["api_key"] = config.api_key
    if config.base_url:
        kwargs["base_url"] = config.base_url
    return ChatOpenAI(**kwargs)


def _build_mock(config: LlmProviderConfig) -> SupportsInvoke:
    return EchoChatModel(model=config.model or "mock-echo")


def _build_local(config: LlmProviderConfig) -> SupportsInvoke:
    return _build_chat_openai(
        LlmProviderConfig(
            provider="local",
            model=config.model or env_str("MODEL_NAME", "qwen3:8b"),
            temperature=config.temperature or env_float("TEMPERATURE", 0.3),
            api_key=config.api_key or env_str("MODEL_KEY", "local"),
            base_url=config.base_url or _ensure_v1_suffix(env_str("MODEL_URL", "http://127.0.0.1:11434")),
            extra={
                **dict(config.extra),
                "extra_body": {
                    "num_ctx": env_int("NUM_CTX", 16384),
                    "num_predict": env_int("NUM_PREDICT", 1024),
                },
            },
        )
    )


def _build_qwen(config: LlmProviderConfig) -> SupportsInvoke:
    return _build_chat_openai(
        LlmProviderConfig(
            provider="qwen",
            model=config.model or env_str("QWEN_MODEL_NAME", "qwen-plus"),
            temperature=config.temperature or env_float("TEMPERATURE", 0.3),
            api_key=config.api_key or env_str("QWEN_KEY"),
            base_url=config.base_url or env_str("QWEN_MODEL_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            extra=config.extra,
        )
    )


def _build_doubao(config: LlmProviderConfig) -> SupportsInvoke:
    return _build_chat_openai(
        LlmProviderConfig(
            provider="doubao",
            model=config.model or env_str("DOUBAO_MODEL_NAME", "ark-code-latest"),
            temperature=config.temperature or env_float("TEMPERATURE", 0.3),
            api_key=config.api_key or env_str("DOUBAO_MODEL_KEY"),
            base_url=config.base_url or env_str("DOUBAO_MODEL_URL", "https://ark.cn-beijing.volces.com/api/coding/v3"),
            extra=config.extra,
        )
    )


def _build_kimi(config: LlmProviderConfig) -> SupportsInvoke:
    return _build_chat_openai(
        LlmProviderConfig(
            provider="kimi",
            model=config.model or env_str("KIMI_MODEL_NAME", "kimi-k2-0711-preview"),
            temperature=config.temperature or env_float("TEMPERATURE", 0.3),
            api_key=config.api_key or env_str("KIMI_MODEL_KEY"),
            base_url=config.base_url or env_str("KIMI_MODEL_URL", "https://api.moonshot.cn/v1"),
            extra=config.extra,
        )
    )


def _ensure_v1_suffix(base_url: str | None) -> str | None:
    if base_url is None:
        return None
    normalized = base_url.rstrip("/")
    if normalized.endswith("/v1"):
        return normalized
    return normalized + "/v1"


def register_default_llms() -> None:
    GLOBAL_LLM_REGISTRY.register("mock", _build_mock)
    GLOBAL_LLM_REGISTRY.register("local", _build_local)
    GLOBAL_LLM_REGISTRY.register("qwen", _build_qwen)
    GLOBAL_LLM_REGISTRY.register("doubao", _build_doubao)
    GLOBAL_LLM_REGISTRY.register("kimi", _build_kimi)
