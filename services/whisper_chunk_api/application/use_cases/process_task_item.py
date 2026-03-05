import json
import logging

from whisper_chunk_api.application.dto import ChunkTranscribeCommand, WhisperTaskItem
from whisper_chunk_api.application.ports import (
    SummaryEmailSenderPort,
    TranscriptPostprocessorPort,
    TranscriptSummaryPort,
)

logger = logging.getLogger("whisper_worker.use_case")


class ProcessWhisperTaskItemUseCase:
    def __init__(
        self,
        *,
        task_repository,
        transcribe_use_case,
        text_postprocessor: TranscriptPostprocessorPort | None = None,
        summary_builder: TranscriptSummaryPort | None = None,
        summary_email_sender: SummaryEmailSenderPort | None = None,
    ):
        self._task_repository = task_repository
        self._transcribe_use_case = transcribe_use_case
        self._text_postprocessor = text_postprocessor
        self._summary_builder = summary_builder
        self._summary_email_sender = summary_email_sender

    def execute(self, task: WhisperTaskItem) -> WhisperTaskItem:
        try:
            logger.info(
                "Start transcribe task_id=%s backend=%s model=%s task=%s chunk_seconds=%s language=%s",
                task.id,
                task.backend,
                task.cloud_model if task.backend == "cloud" else task.model,
                task.task,
                task.chunk_seconds,
                task.language,
            )
            result = self._transcribe_use_case.execute(
                ChunkTranscribeCommand(
                    path=task.audio_path,
                    model=task.model,
                    language=task.language,
                    task=task.task,
                    chunk_seconds=task.chunk_seconds,
                    backend=task.backend,
                    cloud_model=task.cloud_model,
                    prompt=task.prompt,
                    temperature=task.temperature,
                )
            )
            raw_text = result.get("text", "")
            postprocessed_text = raw_text
            if self._text_postprocessor is not None:
                try:
                    postprocessed_text = self._text_postprocessor.postprocess(text=raw_text, language=task.language)
                except Exception as post_err:
                    logger.exception("Postprocess failed task_id=%s error=%s", task.id, post_err)

            result_payload = dict(result)
            result_payload["raw_text"] = raw_text
            result_payload["postprocessed_text"] = postprocessed_text
            result_payload["text"] = postprocessed_text
            summary_text = None
            if self._summary_builder is not None:
                try:
                    summary_text = self._summary_builder.summarize(text=postprocessed_text)
                except Exception as summary_err:
                    logger.exception("Summary failed task_id=%s error=%s", task.id, summary_err)
            if summary_text is not None:
                result_payload["summary"] = summary_text
            if summary_text and self._summary_email_sender and task.requester_email:
                try:
                    self._summary_email_sender.send_summary(
                        recipient=task.requester_email,
                        event_id=task.event_id,
                        summary=summary_text,
                    )
                except Exception as email_err:
                    logger.exception("Summary email failed task_id=%s error=%s", task.id, email_err)
            return self._task_repository.mark_done(
                task.id,
                transcript_text=postprocessed_text,
                transcript_json=json.dumps(result_payload, ensure_ascii=False),
                summary=summary_text,
            )
        except Exception as err:
            logger.exception("Transcribe failed task_id=%s error=%s", task.id, err)
            return self._task_repository.mark_failed(task.id, error_message=str(err))
