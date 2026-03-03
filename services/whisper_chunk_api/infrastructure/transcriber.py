from pathlib import Path
from typing import Any

from openai import OpenAI

from whisper_chunk_api.application.errors import ApplicationError


class BackendAwareTranscriber:
    def __init__(self, *, openai_api_key: str, openai_base_url: str | None, local_device: str = "cpu"):
        self._openai_api_key = openai_api_key
        self._openai_base_url = openai_base_url
        self._local_device = local_device
        self._model_cache: dict[tuple[str, str], Any] = {}

    def _get_local_model(self, model_name: str) -> Any:
        key = (model_name, self._local_device)
        if key not in self._model_cache:
            import whisper

            self._model_cache[key] = whisper.load_model(model_name, device=self._local_device)
        return self._model_cache[key]

    def _transcribe_cloud(
        self,
        *,
        chunk_path: Path,
        model_name: str,
        language: str | None,
        task: str,
        prompt: str | None,
        temperature: float,
    ) -> str:
        if not self._openai_api_key:
            raise ApplicationError("OPENAI_API_KEY is not set for backend=cloud", status_code=400)

        client_kwargs: dict[str, Any] = {"api_key": self._openai_api_key}
        if self._openai_base_url:
            client_kwargs["base_url"] = self._openai_base_url
        client = OpenAI(**client_kwargs)

        with chunk_path.open("rb") as audio_file:
            if task == "translate":
                response = client.audio.translations.create(
                    model=model_name,
                    file=audio_file,
                    prompt=prompt,
                    temperature=temperature,
                )
            else:
                response = client.audio.transcriptions.create(
                    model=model_name,
                    file=audio_file,
                    language=language,
                    prompt=prompt,
                    temperature=temperature,
                )
        return (getattr(response, "text", "") or "").strip()

    def transcribe(
        self,
        *,
        chunk_path: Path,
        backend: str,
        model: str,
        cloud_model: str,
        language: str | None,
        task: str,
        prompt: str | None,
        temperature: float,
    ) -> str:
        if backend == "cloud":
            return self._transcribe_cloud(
                chunk_path=chunk_path,
                model_name=cloud_model,
                language=language,
                task=task,
                prompt=prompt,
                temperature=temperature,
            )

        local_model = self._get_local_model(model)
        result = local_model.transcribe(str(chunk_path), language=language, task=task)
        return (result.get("text") or "").strip()
