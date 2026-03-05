from whisper_chunk_api.worker import run_once, run_poll_cycle


class FakeTask:
    def __init__(self, task_id: str):
        self.id = task_id


class FakeRepo:
    def __init__(self):
        self._served = False

    def claim_ready(self, limit: int):
        if self._served:
            return []
        self._served = True
        return [FakeTask("task-1")]


class FakeUseCase:
    def __init__(self):
        self.processed = []

    def execute(self, task):
        self.processed.append(task.id)


def test_worker_run_once_claims_and_processes_tasks(monkeypatch):
    fake_repo = FakeRepo()
    fake_use_case = FakeUseCase()
    monkeypatch.setattr("whisper_chunk_api.worker.build_processor", lambda: (fake_repo, fake_use_case))

    count = run_once(limit=10)

    assert count == 1
    assert fake_use_case.processed == ["task-1"]


def test_run_poll_cycle_uses_requested_worker_count(monkeypatch):
    calls = {"count": 0}

    def fake_run_once(limit: int) -> int:
        calls["count"] += 1
        return 1

    monkeypatch.setattr("whisper_chunk_api.worker.run_once", fake_run_once)

    processed = run_poll_cycle(worker_count=3, limit=10)

    assert processed == 3
    assert calls["count"] == 3
