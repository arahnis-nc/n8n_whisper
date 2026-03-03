from pathlib import Path

from whisper_chunk_api.application.dto import ChunkTranscribeCommand
from whisper_chunk_api.application.use_cases.transcribe_chunks import TranscribeChunksUseCase


class FakePathResolver:
    def resolve_input_file(self, relative_path: str) -> Path:
        return Path("/data/records") / relative_path

    def to_relative(self, absolute_path: Path) -> str:
        return str(absolute_path).replace("/data/records/", "")


class FakeChunker:
    def chunk_to_wav(self, source: Path, chunk_seconds: int, output_dir: Path) -> list[Path]:
        return [output_dir / "chunk_00000.wav", output_dir / "chunk_00001.wav"]


class FakeTranscriber:
    def transcribe(self, **kwargs) -> str:
        return "hello"


class FakeWorkspace:
    def create_temp_dir(self, prefix: str) -> Path:
        return Path("/tmp/whisper_chunks")

    def remove_tree(self, target: Path) -> None:
        pass


def test_transcribe_chunks_use_case_aggregates_chunks():
    use_case = TranscribeChunksUseCase(
        path_resolver=FakePathResolver(),
        chunker=FakeChunker(),
        transcriber=FakeTranscriber(),
        workspace=FakeWorkspace(),
    )
    result = use_case.execute(
        ChunkTranscribeCommand(
            path="audio/test.wav",
            model="tiny",
            language=None,
            task="transcribe",
            chunk_seconds=120,
            backend="local",
            cloud_model="whisper-1",
            prompt=None,
            temperature=0.0,
        )
    )

    assert result["chunks_count"] == 2
    assert result["text"] == "hello\nhello"
