const form = document.getElementById("status-form");
const eventIdInput = document.getElementById("event-id");
const secretInput = document.getElementById("secret");
const checkBtn = document.getElementById("check-btn");
const resultBlock = document.getElementById("result");
const errorBlock = document.getElementById("error");
const smtpRefreshBtn = document.getElementById("smtp-refresh-btn");
const smtpSummary = document.getElementById("smtp-summary");

function setLoading(isLoading) {
  checkBtn.disabled = isLoading;
  checkBtn.textContent = isLoading ? "Проверка..." : "Проверить";
}

function showResult(text) {
  resultBlock.textContent = text;
  resultBlock.classList.remove("hidden");
}

function showError(text) {
  errorBlock.textContent = text;
  errorBlock.classList.remove("hidden");
}

function clearMessages() {
  resultBlock.textContent = "";
  errorBlock.textContent = "";
  resultBlock.classList.add("hidden");
  errorBlock.classList.add("hidden");
}

function formatStatus(payload) {
  const lines = [];
  const summary = payload.whisper_summary || "Саммари пока не готово.";
  const formatted = payload.whisper_formatted_text || payload.whisper_transcript || "Расшифровка пока не готова.";

  lines.push("summary:");
  lines.push(summary);
  lines.push("");
  lines.push("formatted_text:");
  lines.push(formatted);
  return lines.join("\n");
}

function prefillFromQuery() {
  const params = new URLSearchParams(window.location.search);
  const eventId = params.get("event_id");
  if (eventId) {
    eventIdInput.value = eventId;
  }
}

function setSmtpLoading(isLoading) {
  smtpRefreshBtn.disabled = isLoading;
  smtpRefreshBtn.textContent = isLoading ? "Обновление..." : "Обновить";
}

function renderSmtpSummary(payload) {
  smtpSummary.textContent =
    `Всего: ${payload.total}. Pending: ${payload.pending}, Sending: ${payload.sending}, ` +
    `Sent: ${payload.sent}, С ошибками: ${payload.with_errors}.`;
}

async function refreshSmtpDiagnostics() {
  setSmtpLoading(true);
  try {
    const response = await fetch("/audio-ingest/notifications/diagnostics");
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      smtpSummary.textContent = payload.detail || "Не удалось получить состояние SMTP-очереди.";
      return;
    }
    renderSmtpSummary(payload);
  } catch (error) {
    smtpSummary.textContent = "Сервис недоступен, не удалось получить состояние SMTP-очереди.";
  } finally {
    setSmtpLoading(false);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearMessages();

  const eventId = eventIdInput.value.trim();
  const secret = secretInput.value.trim();

  if (!eventId) {
    showError("Укажите event_id.");
    return;
  }
  if (!secret) {
    showError("Укажите secret.");
    return;
  }

  setLoading(true);
  try {
    const response = await fetch(`/audio-ingest/outbox/${encodeURIComponent(eventId)}/status?secret=${encodeURIComponent(secret)}`);
    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      const message = payload.detail || "Не удалось получить статус.";
      showError(message);
      return;
    }

    showResult(formatStatus(payload));
  } catch (error) {
    showError("Сервис недоступен, попробуйте позже.");
  } finally {
    setLoading(false);
  }
});

prefillFromQuery();
smtpRefreshBtn.addEventListener("click", refreshSmtpDiagnostics);
refreshSmtpDiagnostics();
