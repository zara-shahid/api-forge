const BASE_URL = "http://127.0.0.1:8000";

const promptInput = document.getElementById("promptInput");
const forgeBtn = document.getElementById("forgeBtn");
const resultEl = document.getElementById("result");

forgeBtn.addEventListener("click", async () => {
  const prompt = promptInput.value.trim();
  if (!prompt) return;

  forgeBtn.disabled = true;
  resultEl.textContent = "Generating...";

  try {
    const res = await fetch(
      `${BASE_URL}/generate?prompt=${encodeURIComponent(prompt)}`,
      { method: "POST" }
    );
    if (!res.ok) throw new Error(`Server responded ${res.status}`);
    const data = await res.json();

    // TODO: replace with the real Screen 2 (stat plates, entity cards,
    // embedded Swagger view) instead of raw JSON.
    resultEl.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    resultEl.textContent = `Generation failed: ${err.message}`;
  } finally {
    forgeBtn.disabled = false;
  }
});
