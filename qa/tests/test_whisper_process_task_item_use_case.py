from whisper_chunk_api.application.dto import WhisperTaskItem
from whisper_chunk_api.application.use_cases.process_task_item import ProcessWhisperTaskItemUseCase


class FakeTaskRepository:
    def __init__(self):
        self.done = {}

    def mark_done(self, task_id: str, *, transcript_text: str, transcript_json: str, summary: str | None):
        self.done = {
            "task_id": task_id,
            "transcript_text": transcript_text,
            "transcript_json": transcript_json,
            "summary": summary,
        }
        return WhisperTaskItem(
            id=task_id,
            audio_path="calls/sample.mp3",
            event_id="evt-1",
            requester_email="user@example.com",
            status="done",
            backend="cloud",
            model="tiny",
            cloud_model="whisper-1",
            task="transcribe",
            chunk_seconds=300,
            language="ru",
            prompt=None,
            temperature=0.0,
            transcript_text=transcript_text,
            transcript_json=transcript_json,
            summary=summary,
            error=None,
        )

    def mark_failed(self, task_id: str, *, error_message: str):
        return WhisperTaskItem(
            id=task_id,
            audio_path="calls/sample.mp3",
            event_id="evt-1",
            requester_email="user@example.com",
            status="failed",
            backend="cloud",
            model="tiny",
            cloud_model="whisper-1",
            task="transcribe",
            chunk_seconds=300,
            language="ru",
            prompt=None,
            temperature=0.0,
            transcript_text=None,
            transcript_json=None,
            summary=None,
            error=error_message,
        )


class FakeTranscribeUseCase:
    def execute(self, command):
        return {"text": "привет как дела"}


class FakePostprocessor:
    def postprocess(self, *, text: str, language: str | None) -> str:
        assert language == "ru"
        assert text == "привет как дела"
        return "Спикер 1: Привет, как дела?"


class FakeSummarizer:
    def summarize(self, *, text: str) -> str:
        assert text == "Спикер 1: Привет, как дела?"
        return "## Решения\n- Поздороваться.\n\n## Открытые вопросы\n- Нет.\n\n## Action items\n- Нет.\n\n## Риски\n- Нет."


class FakeSummaryEmailSender:
    def __init__(self):
        self.calls = []

    def send_summary(self, *, recipient: str, event_id: str | None, summary: str) -> None:
        self.calls.append((recipient, event_id, summary))


def test_process_task_item_use_case_applies_postprocess_before_save():
    task = WhisperTaskItem(
        id="task-1",
        audio_path="calls/sample.mp3",
        event_id="evt-1",
        requester_email="user@example.com",
        status="processing",
        backend="cloud",
        model="tiny",
        cloud_model="whisper-1",
        task="transcribe",
        chunk_seconds=300,
        language="ru",
        prompt=None,
        temperature=0.0,
        transcript_text=None,
        transcript_json=None,
        error=None,
    )
    repo = FakeTaskRepository()
    email_sender = FakeSummaryEmailSender()
    use_case = ProcessWhisperTaskItemUseCase(
        task_repository=repo,
        transcribe_use_case=FakeTranscribeUseCase(),
        text_postprocessor=FakePostprocessor(),
        summary_builder=FakeSummarizer(),
        summary_email_sender=email_sender,
    )

    result = use_case.execute(task)

    assert result.status == "done"
    assert repo.done["transcript_text"] == "Спикер 1: Привет, как дела?"
    assert '"raw_text": "привет как дела"' in repo.done["transcript_json"]
    assert repo.done["summary"].startswith("## Решения")
    assert email_sender.calls
    recipient, event_id, summary = email_sender.calls[0]
    assert recipient == "user@example.com"
    assert event_id == "evt-1"
    assert summary.startswith("## Решения")
