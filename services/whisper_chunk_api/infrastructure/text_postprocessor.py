import logging
from typing import Any

from openai import OpenAI

logger = logging.getLogger("whisper_worker.postprocess")


class NoopTranscriptPostprocessor:
    def postprocess(self, *, text: str, language: str | None) -> str:
        return text


class OpenAiTranscriptPostprocessor:
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

    def postprocess(self, *, text: str, language: str | None) -> str:
        if not text.strip():
            return text
        if not self._api_key:
            logger.warning("OpenAI API key is missing, skip transcript postprocess")
            return text
        logger.info("Start transcript postprocess chars=%s language=%s model=%s", len(text), language, self._model)

        client_kwargs: dict[str, Any] = {"api_key": self._api_key}
        if self._base_url:
            client_kwargs["base_url"] = self._base_url
        client = OpenAI(**client_kwargs)

        language_hint = language or "unknown"
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты редактор расшифровок звонков. Разбей текст на реплики спикеров "
                    "в формате 'Спикер 1:' / 'Спикер 2:' и приведи пунктуацию в порядок. "
                    "Исправляй явные ошибки распознавания и искаженные слова по контексту "
                    "технической речи. Не добавляй фактов, которых нет в исходном тексте. "
                    "Если не уверен в корректировке, оставь исходный вариант."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Язык исходного текста: {language_hint}\n\n"
                    "Верни только итоговый текст с репликами спикеров.\n\n"
                    f"Исходный текст:\n{text}"
                ),
            },
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
                content = (response.choices[0].message.content or "").strip()
                final_text = content or text
                logger.info("Transcript postprocess completed chars=%s model=%s", len(final_text), model_name)
                return final_text
            except Exception as err:
                last_error = err
                logger.warning("Transcript postprocess model failed model=%s error=%s", model_name, err)

        if last_error is not None:
            raise last_error
        return text
