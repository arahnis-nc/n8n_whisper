from pathlib import Path

from parakeet_api.application.dto import TranscribeCommand
from parakeet_api.application.use_cases.transcribe_audio import TranscribeAudioUseCase


class FakeResolver:
    def to_relative(self, absolute_path: Path) -> str:
        return "audio/test.wav"


class FakeStorage:
    def __init__(self):
        self.deleted = False

    def delete_if_exists(self, target: Path) -> None:
        self.deleted = True


class FakeTranscriber:
    def transcribe(self, source_path: Path, model_name: str, language: str | None) -> str:
        return "sample text"


def test_transcribe_audio_use_case_returns_contract():
    storage = FakeStorage()
    use_case = TranscribeAudioUseCase(
        transcriber=FakeTranscriber(),
        path_resolver=FakeResolver(),
        upload_storage=storage,
    )

    result = use_case.execute(
        TranscribeCommand(
            source_path=Path("/tmp/upload.wav"),
            source_is_temporary=True,
            model="nvidia/parakeet-tdt-0.6b-v3",
            language=None,
        )
    )

    assert result["text"] == "sample text"
    assert result["input_path"] == "audio/test.wav"
    assert storage.deleted is True
