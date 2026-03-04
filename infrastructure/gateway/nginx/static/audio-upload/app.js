const form = document.getElementById("upload-form");
const emailInput = document.getElementById("email");
const fileInput = document.getElementById("file");
const submitBtn = document.getElementById("submit-btn");
const resultBlock = document.getElementById("result");
const errorBlock = document.getElementById("error");

function setLoading(isLoading) {
  submitBtn.disabled = isLoading;
  submitBtn.textContent = isLoading ? "Отправка..." : "Отправить";
}

function showResult(text) {
  resultBlock.textContent = text;
  resultBlock.classList.remove("hidden");
}

function showResultHtml(html) {
  resultBlock.innerHTML = html;
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

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearMessages();

  const email = emailInput.value.trim();
  const file = fileInput.files && fileInput.files[0];

  if (!email) {
    showError("Укажите email.");
    return;
  }
  if (!file) {
    showError("Выберите файл.");
    return;
  }

  const formData = new FormData();
  formData.append("email", email);
  formData.append("file", file);

  setLoading(true);
  try {
    const response = await fetch("/audio-ingest/ingest", {
      method: "POST",
      body: formData,
    });

    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const message = payload.detail || "Ошибка при отправке файла.";
      showError(message);
      return;
    }

    const secret = payload.secret ?? payload.access_secret;
    if (!secret) {
      showError("Сервис вернул event_id без secret. Перезапустите audio-ingest с новым кодом.");
      return;
    }

    const statusUrl = `/audio-status?event_id=${encodeURIComponent(payload.event_id)}`;
    showResultHtml(
      [
        `<p>Файл принят.</p>`,
        `<p><strong>event_id:</strong> <code>${payload.event_id}</code></p>`,
        `<p><strong>secret:</strong> <code>${secret}</code></p>`,
        `<p>Сохраните secret: он нужен для проверки статуса.</p>`,
        `<p><a href="${statusUrl}">Перейти на страницу проверки статуса</a></p>`,
      ].join("")
    );
    form.reset();
    form.classList.add("hidden");
  } catch (error) {
    showError("Сервис недоступен, попробуйте позже.");
  } finally {
    setLoading(false);
  }
});

