import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import whisper
from fastapi import HTTPException

from whisper_api.core.settings import Settings


class SpeechService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._model_cache: dict[str, Any] = {}
        self._diarization_pipeline: Any | None = None

    def resolve_relative_source(self, relative_path: str) -> Path:
        candidate = (self.settings.records_dir / relative_path).resolve()
        if not candidate.is_file():
            raise HTTPException(status_code=404, detail=f"File not found: {relative_path}")
        if self.settings.records_dir not in candidate.parents:
            raise HTTPException(status_code=400, detail="Path must stay inside records directory")
        return candidate

    def save_upload(self, filename: str | None, content: bytes) -> Path:
        self.settings.uploads_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(filename or "audio.bin").name
        target = self.settings.uploads_dir / f"{uuid4().hex}_{safe_name}"
        target.write_bytes(content)
        return target

    def transcribe(
        self,
        source_path: Path,
        model_name: str,
        language: str | None,
        task: str,
        save_txt: bool,
        save_json: bool,
        delete_source: bool,
        diarize: bool,
        min_speakers: int | None,
        max_speakers: int | None,
    ) -> dict[str, Any]:
        try:
            model = self._get_model(model_name)
            result = model.transcribe(
                str(source_path),
                language=language,
                task=task,
                word_timestamps=diarize,
            )
            diarization_segments = None
            if diarize:
                diarization_segments = self._run_diarization(
                    source_path=source_path,
                    result=result,
                    min_speakers=min_speakers,
                    max_speakers=max_speakers,
                )
            outputs = self._write_outputs(source_path, result, save_txt=save_txt, save_json=save_json)
            return {
                "text": (result.get("text") or "").strip(),
                "language": result.get("language"),
                "model": model_name,
                "task": task,
                "input_path": str(source_path.relative_to(self.settings.records_dir)),
                "txt_path": outputs["txt_path"],
                "json_path": outputs["json_path"],
                "result": result,
                "diarization": diarization_segments,
            }
        finally:
            if delete_source and source_path.exists():
                source_path.unlink(missing_ok=True)

    def _get_model(self, model_name: str):
        if model_name not in self._model_cache:
            self.settings.whisper_cache_dir.mkdir(parents=True, exist_ok=True)
            try:
                self._model_cache[model_name] = whisper.load_model(
                    model_name,
                    download_root=str(self.settings.whisper_cache_dir),
                )
            except RuntimeError as exc:
                if "checksum" not in str(exc).lower():
                    raise
                for stale_file in self.settings.whisper_cache_dir.glob("*.pt"):
                    stale_file.unlink(missing_ok=True)
                self._model_cache[model_name] = whisper.load_model(
                    model_name,
                    download_root=str(self.settings.whisper_cache_dir),
                )
        return self._model_cache[model_name]

    def _get_diarization_pipeline(self):
        if self._diarization_pipeline is None:
            if not self.settings.huggingface_token:
                raise HTTPException(
                    status_code=400,
                    detail="Diarization requires HUGGINGFACE_TOKEN in whisper container environment.",
                )
            from whisperx.diarize import DiarizationPipeline
            import torch
            import huggingface_hub
            import huggingface_hub.file_download as hub_file_download

            # Compatibility bridge: some pyannote/whisperx stacks still pass
            # `use_auth_token`, while newer huggingface_hub expects `token`.
            original_download = huggingface_hub.hf_hub_download

            def _hf_hub_download_compat(*args, **kwargs):
                if "use_auth_token" in kwargs and "token" not in kwargs:
                    kwargs["token"] = kwargs.pop("use_auth_token")
                return original_download(*args, **kwargs)

            huggingface_hub.hf_hub_download = _hf_hub_download_compat
            hub_file_download.hf_hub_download = _hf_hub_download_compat

            try:
                # Compatibility fix for pyannote checkpoints with newer PyTorch defaults.
                torch.serialization.add_safe_globals([torch.torch_version.TorchVersion])
                self._diarization_pipeline = DiarizationPipeline(
                    use_auth_token=self.settings.huggingface_token,
                    device=self.settings.whisper_device,
                )
            except Exception as exc:  # pragma: no cover - depends on external HF state
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Cannot initialize diarization model. "
                        "Check HUGGINGFACE_TOKEN and accept gated model terms for "
                        "pyannote/speaker-diarization-3.1 and pyannote/segmentation-3.0. "
                        f"Underlying error: {exc}"
                    ),
                ) from exc
        return self._diarization_pipeline

    def _run_diarization(
        self,
        source_path: Path,
        result: dict[str, Any],
        min_speakers: int | None,
        max_speakers: int | None,
    ) -> list[dict[str, Any]]:
        import whisperx

        audio = whisperx.load_audio(str(source_path))
        diarize_model = self._get_diarization_pipeline()
        diarize_df = diarize_model(
            audio,
            min_speakers=min_speakers,
            max_speakers=max_speakers,
        )
        return self._assign_speakers_to_segments(result, diarize_df)

    @staticmethod
    def _assign_speakers_to_segments(result: dict[str, Any], diarize_df: Any):
        diarize_items: list[tuple[float, float, str]] = []
        for row in diarize_df.itertuples(index=False):
            start = float(getattr(row, "start"))
            end = float(getattr(row, "end"))
            speaker = str(getattr(row, "speaker"))
            diarize_items.append((start, end, speaker))

        def pick_speaker(start: float, end: float) -> str | None:
            midpoint = (start + end) / 2.0
            for d_start, d_end, d_speaker in diarize_items:
                if d_start <= midpoint <= d_end:
                    return d_speaker
            best_speaker = None
            best_overlap = 0.0
            for d_start, d_end, d_speaker in diarize_items:
                overlap = max(0.0, min(end, d_end) - max(start, d_start))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = d_speaker
            return best_speaker

        for segment in result.get("segments", []):
            seg_start = float(segment.get("start", 0.0))
            seg_end = float(segment.get("end", seg_start))
            speaker = pick_speaker(seg_start, seg_end)
            if speaker:
                segment["speaker"] = speaker
                if isinstance(segment.get("words"), list):
                    for word in segment["words"]:
                        w_start = float(word.get("start", seg_start))
                        w_end = float(word.get("end", w_start))
                        w_speaker = pick_speaker(w_start, w_end)
                        if w_speaker:
                            word["speaker"] = w_speaker

        return [
            {"start": d_start, "end": d_end, "speaker": d_speaker}
            for d_start, d_end, d_speaker in diarize_items
        ]

    def _write_outputs(
        self,
        source_path: Path,
        result: dict[str, Any],
        save_txt: bool,
        save_json: bool,
    ) -> dict[str, str | None]:
        self.settings.transcripts_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        base = f"{source_path.stem}_{stamp}_{uuid4().hex[:8]}"
        txt_path = self.settings.transcripts_dir / f"{base}.txt"
        json_path = self.settings.transcripts_dir / f"{base}.json"

        written_txt = None
        written_json = None

        if save_txt:
            txt_path.write_text((result.get("text") or "").strip(), encoding="utf-8")
            written_txt = str(txt_path.relative_to(self.settings.records_dir))
        if save_json:
            json_path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
            written_json = str(json_path.relative_to(self.settings.records_dir))

        return {"txt_path": written_txt, "json_path": written_json}

