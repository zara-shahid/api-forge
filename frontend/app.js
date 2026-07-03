const BASE_URL = "http://127.0.0.1:8000";

// ---- Element refs ----
const promptView = document.getElementById("promptView");
const progressView = document.getElementById("progressView");
const resultView = document.getElementById("resultView");
const errorView = document.getElementById("errorView");

const promptInput = document.getElementById("promptInput");
const promptHint = document.getElementById("promptHint");
const forgeBtn = document.getElementById("forgeBtn");
const chipRow = document.getElementById("chipRow");

const statRow = document.getElementById("statRow");
const openDocsBtn = document.getElementById("openDocsBtn");
const forgeAnotherBtn = document.getElementById("forgeAnotherBtn");

const errorMessage = document.getElementById("errorMessage");
const retryBtn = document.getElementById("retryBtn");

const stageEls = Array.from(document.querySelectorAll(".stage"));

// ---- View switching ----
function showView(view) {
  [promptView, progressView, resultView, errorView].forEach((v) => {
    v.classList.toggle("forge-panel__body--hidden", v !== view);
  });
}

// ---- Example chips ----
chipRow.addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  promptInput.value = chip.dataset.prompt;
  promptInput.focus();
});

// ---- Assembly line animation ----
// The real backend does this as ONE /generate call, but the guide's
// UI design calls for a visible 4-stage pipeline rather than a bare
// spinner. We advance stages 1-3 on a timer while the real fetch is
// in flight, then snap straight to "complete" the moment the real
// response comes back -- so the trail always finishes in sync with
// reality, it just doesn't sit idle while waiting.
let stageTimer = null;

function resetStages() {
  stageEls.forEach((el) => el.classList.remove("is-active", "is-complete"));
}

function setStage(index, state) {
  const el = stageEls[index];
  if (!el) return;
  el.classList.remove("is-active", "is-complete");
  el.classList.add(state);
}

function advanceStagesWhileWaiting() {
  resetStages();
  let current = 0;
  setStage(0, "is-active");

  stageTimer = setInterval(() => {
    setStage(current, "is-complete");
    current += 1;
    // Stop advancing automatically at "Seed data" (index 2) -- "Mount
    // routes" only completes once we actually have a response, since
    // mounting is the literal last thing /generate does server-side.
    if (current <= 2) {
      setStage(current, "is-active");
    } else {
      clearInterval(stageTimer);
    }
  }, 900);
}

function completeAllStages() {
  if (stageTimer) clearInterval(stageTimer);
  stageEls.forEach((el) => {
    el.classList.remove("is-active");
    el.classList.add("is-complete");
  });
}

// ---- Forge flow ----
async function forge() {
  const prompt = promptInput.value.trim();
  if (!prompt) {
    promptHint.textContent = "Describe a backend first — try one of the examples below.";
    return;
  }
  promptHint.textContent = "";

  showView(progressView);
  advanceStagesWhileWaiting();

  try {
    const res = await fetch(
      `${BASE_URL}/generate?${new URLSearchParams({ prompt })}`,
      { method: "POST" }
    );

    const data = await res.json().catch(() => null);

    if (!res.ok) {
      const detail = (data && data.detail) || `Server responded ${res.status}`;
      throw new Error(detail);
    }

    completeAllStages();
    // Brief pause so the last stage's fill is actually visible before
    // switching views -- otherwise "Mount routes" completes and
    // disappears in the same frame.
    await new Promise((resolve) => setTimeout(resolve, 500));

    renderResult(data);
    showView(resultView);
  } catch (err) {
    if (stageTimer) clearInterval(stageTimer);
    errorMessage.textContent = `${err.message}. Check that the server is running and try again.`;
    showView(errorView);
  }
}

function renderResult(data) {
  statRow.innerHTML = "";
  const stats = [
    { value: data.entity_count, label: "Entities" },
    { value: data.route_count, label: "Routes" },
    { value: data.api_id, label: "API ID" },
  ];

  stats.forEach((stat) => {
    const plate = document.createElement("div");
    plate.className = "stat-plate";
    plate.innerHTML = `
      <span class="stat-plate__value">${stat.value}</span>
      <span class="stat-plate__label">${stat.label}</span>
    `;
    statRow.appendChild(plate);
  });

  openDocsBtn.href = `${BASE_URL}${data.docs_url}`;
}

// ---- Wiring ----
forgeBtn.addEventListener("click", forge);

promptInput.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
    forge();
  }
});

forgeAnotherBtn.addEventListener("click", () => {
  promptInput.value = "";
  resetStages();
  showView(promptView);
  promptInput.focus();
});

retryBtn.addEventListener("click", () => {
  resetStages();
  showView(promptView);
  promptInput.focus();
});