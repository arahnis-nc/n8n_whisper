from pathlib import Path
from typing import Any


class NemoParakeetTranscriber:
    def __init__(self, device: str = "cpu"):
        self._device = device
        self._model_cache: dict[tuple[str, str], Any] = {}

    def _get_model(self, model_name: str):
        key = (model_name, self._device)
        if key not in self._model_cache:
            from nemo.collections import asr as nemo_asr

            model = nemo_asr.models.ASRModel.from_pretrained(model_name=model_name, map_location=self._device)
            model.freeze()
            self._model_cache[key] = model
        return self._model_cache[key]

    def transcribe(self, source_path: Path, model_name: str, language: str | None) -> str:
        model = self._get_model(model_name=model_name)
        outputs = model.transcribe(audio=[str(source_path)], batch_size=1, verbose=False)
        first = outputs[0] if outputs else ""
        text = first.text if hasattr(first, "text") else str(first)
        return text
