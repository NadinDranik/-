from abc import ABC, abstractmethod
import re
from dataclasses import dataclass

from app.config import get_settings


@dataclass
class LLMResponse:
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class EmbeddingResponse:
    embedding: list[float]
    model: str
    total_tokens: int = 0


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> LLMResponse:
        pass

    @abstractmethod
    async def embed(self, text: str) -> EmbeddingResponse:
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._embedding_model = settings.embedding_model
        self._chat_model = "gpt-4o"

    @property
    def provider_name(self) -> str:
        return "openai"

    async def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> LLMResponse:
        response = await self.client.chat.completions.create(
            model=self._chat_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        usage = response.usage
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
        )

    async def embed(self, text: str) -> EmbeddingResponse:
        response = await self.client.embeddings.create(model=self._embedding_model, input=text)
        data = response.data[0]
        return EmbeddingResponse(
            embedding=data.embedding,
            model=response.model,
            total_tokens=response.usage.total_tokens if response.usage else 0,
        )


class AnthropicProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        from anthropic import AsyncAnthropic

        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._chat_model = "claude-sonnet-4-20250514"
        self._openai = OpenAIProvider()

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> LLMResponse:
        response = await self.client.messages.create(
            model=self._chat_model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        content = "".join(block.text for block in response.content if hasattr(block, "text"))
        return LLMResponse(
            content=content,
            model=response.model,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
        )

    async def embed(self, text: str) -> EmbeddingResponse:
        return await self._openai.embed(text)


class YandexGPTProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.yandex_api_key
        self.folder_id = settings.yandex_folder_id
        self._openai = OpenAIProvider()

    @property
    def provider_name(self) -> str:
        return "yandex"

    async def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> LLMResponse:
        import httpx

        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {"Authorization": f"Api-Key {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt/latest",
            "completionOptions": {"stream": False, "temperature": 0.3, "maxTokens": str(max_tokens)},
            "messages": [
                {"role": "system", "text": system_prompt},
                {"role": "user", "text": user_prompt},
            ],
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        text = data["result"]["alternatives"][0]["message"]["text"]
        return LLMResponse(content=text, model="yandexgpt")

    async def embed(self, text: str) -> EmbeddingResponse:
        import httpx

        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/textEmbedding"
        headers = {"Authorization": f"Api-Key {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "modelUri": f"emb://{self.folder_id}/text-search-doc/latest",
            "text": text,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        return EmbeddingResponse(embedding=data["embedding"], model="yandex-embedding")


class GigaChatProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.credentials = settings.gigachat_credentials
        self._token: str | None = None
        self._openai = OpenAIProvider()

    @property
    def provider_name(self) -> str:
        return "gigachat"

    async def _get_token(self) -> str:
        if self._token:
            return self._token
        import httpx

        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            response = await client.post(
                "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
                headers={
                    "Authorization": f"Basic {self.credentials}",
                    "RqUID": "expert17025",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"scope": "GIGACHAT_API_PERS"},
            )
            response.raise_for_status()
            self._token = response.json()["access_token"]
        return self._token

    async def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> LLMResponse:
        import httpx

        token = await self._get_token()
        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            response = await client.post(
                "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "model": "GigaChat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
        choice = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResponse(
            content=choice,
            model="GigaChat",
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )

    async def embed(self, text: str) -> EmbeddingResponse:
        return await self._openai.embed(text)


class LocalProvider(LLMProvider):
    """Локальный режим: ответы формируются из найденного контекста без внешнего API."""

    @property
    def provider_name(self) -> str:
        return "local"

    async def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> LLMResponse:
        context_match = re.search(r"Контекст:\n(.*?)\n\nВопрос пользователя:", user_prompt, re.DOTALL)
        question_match = re.search(r"Вопрос пользователя:\n(.+)", user_prompt, re.DOTALL)
        context = context_match.group(1).strip() if context_match else ""
        question = question_match.group(1).strip() if question_match else user_prompt

        if not context or context == "Контекст не найден.":
            content = (
                "В базе знаний не найдено достаточно информации для ответа на этот вопрос.\n\n"
                "Рекомендации:\n"
                "1. Загрузите нормативные документы через раздел «Документы»\n"
                "2. Добавьте экспертные ответы в базу знаний\n"
                "3. Настройте API-ключ LLM в `.env` для генерации ответов"
            )
        else:
            kb_section = ""
            doc_section = ""
            for part in context.split("---"):
                part = part.strip()
                if part.startswith("[База знаний"):
                    kb_section += part + "\n\n"
                else:
                    doc_section += part + "\n\n"

            content = f"## Ответ на вопрос\n\n**Вопрос:** {question}\n\n"
            if kb_section:
                content += "### Из базы знаний\n\n" + kb_section[:3000]
            if doc_section:
                content += "### Из нормативных документов\n\n" + doc_section[:4000]
            content += (
                "\n\n---\n*Ответ сформирован на основе загруженных материалов "
                "(локальный режим без внешнего ИИ). Для полноценной генерации настройте API-ключ LLM.*"
            )

        return LLMResponse(content=content, model="local-rag", total_tokens=0)

    async def embed(self, text: str) -> EmbeddingResponse:
        from app.core.embeddings import embed_text

        return EmbeddingResponse(embedding=embed_text(text), model="local-embeddings")


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    providers: dict[str, type[LLMProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "yandex": YandexGPTProvider,
        "gigachat": GigaChatProvider,
        "local": LocalProvider,
    }
    if settings.llm_provider == "local" or not settings.has_llm_api:
        return LocalProvider()
    provider_cls = providers.get(settings.llm_provider, OpenAIProvider)
    return provider_cls()
