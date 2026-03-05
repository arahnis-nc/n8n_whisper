import logging
from typing import Any

from openai import OpenAI

logger = logging.getLogger("whisper_worker.summary")

SUMMARY_PROMPT = """Ты опытный системный аналитик и технический фасилитатор встреч.

Твоя задача — анализировать расшифровку технического обсуждения (meeting transcript)
и формировать структурированное резюме встречи.

Участники обозначены как "Спикер 1", "Спикер 2" и т.д.

Важно:
- Игнорируй лишние слова, шутки, разговорные вставки.
- Выделяй только смысловые решения, вопросы и задачи.
- Если решение обсуждалось и по факту было принято — относить его к "Решения".
- Если обсуждение не завершено — относить к "Открытые вопросы".
- Если участники договорились что-то сделать — это "Action items".
- Если в обсуждении обнаружены архитектурные или проектные проблемы — выделяй их как "Риски".

Не добавляй информацию, которой нет в тексте.

Структура ответа должна быть строго следующей:

## Решения
Краткий список принятых решений.

## Открытые вопросы
Список вопросов, которые требуют уточнения или дальнейшего обсуждения.

## Action items
Список задач с указанием исполнителей (если их можно определить из текста).

## Риски
Технические, архитектурные или организационные риски, выявленные в ходе обсуждения.

Формулируй кратко и по делу."""


class NoopTranscriptSummarizer:
    def summarize(self, *, text: str) -> str:
        return ""


class OpenAiTranscriptSummarizer:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        fallback_model: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.2,
    ):
        self._api_key = api_key
        self._model = model
        self._fallback_model = fallback_model
        self._base_url = base_url
        self._temperature = temperature

    def summarize(self, *, text: str) -> str:
        if not text.strip():
            return ""
        if not self._api_key:
            logger.warning("OpenAI API key is missing, skip transcript summary")
            return ""

        logger.info("Start transcript summary chars=%s model=%s", len(text), self._model)
        client_kwargs: dict[str, Any] = {"api_key": self._api_key}
        if self._base_url:
            client_kwargs["base_url"] = self._base_url
        client = OpenAI(**client_kwargs)
        messages = [
            {"role": "system", "content": SUMMARY_PROMPT},
            {"role": "user", "content": text},
        ]
        models_to_try = [self._model]
        if self._fallback_model and self._fallback_model != self._model:
            models_to_try.append(self._fallback_model)

        last_error: Exception | None = None
        for model_name in models_to_try:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    temperature=self._temperature,
                    messages=messages,
                )
                summary = (response.choices[0].message.content or "").strip()
                logger.info("Transcript summary completed chars=%s model=%s", len(summary), model_name)
                return summary
            except Exception as err:
                last_error = err
                logger.warning("Transcript summary model failed model=%s error=%s", model_name, err)

        if last_error is not None:
            raise last_error
        return ""
