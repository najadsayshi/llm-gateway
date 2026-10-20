from dataclasses import dataclass

from app.config import settings


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    api_key: str | None
    models: frozenset[str]


PROVIDERS = (
    Provider(
        name="openai",
        base_url=settings.openai_api_base,
        api_key=settings.openai_api_key,
        models=frozenset({"gpt-4o-mini", "gpt-4o"}),
    ),
    Provider(
        name="groq",
        base_url=settings.groq_api_base,
        api_key=settings.groq_api_key,
        models=frozenset({"openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"}),
    ),
    Provider(
        name = "openrouter",
        base_url = settings.openrouter_api_base,
        api_key = settings.openrouter_api_key,
        models = frozenset({"minimax/minimax-m3.1-flash:free", "anthropic/claude-opus-5.5", "xingchen-agi/xing4.0-29b-a4b:free"})
        
    )
)

_BY_MODEL = {model: provider for provider in PROVIDERS for model in provider.models}


def provider_for_model(model: str) -> Provider | None:
    return _BY_MODEL.get(model)
