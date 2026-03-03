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

    showResult(`Файл принят. event_id: ${payload.event_id}`);
    form.reset();
    form.classList.add("hidden");
  } catch (error) {
    showError("Сервис недоступен, попробуйте позже.");
  } finally {
    setLoading(false);
  }
});

