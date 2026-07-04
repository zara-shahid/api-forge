const BASE_URL = "http://127.0.0.1:8000";

const presets = {
  ecommerce: "A standard e-commerce backend with products, users, a shopping cart, and a stripe checkout simulation",
  blog: "A blog platform with posts, authors, and comments",
  booking: "A hotel booking system with rooms, guests, and reservations",
  social: "A social feed with users, posts, and likes",
};

const promptInput = document.getElementById("promptInput");
const forgeBtn = document.getElementById("forgeBtn");
const inputMode = document.getElementById("inputMode");
const assembly = document.getElementById("assembly");
const assemblyFill = document.getElementById("assemblyFill");
const stages = document.querySelectorAll(".stage");
const screenPrompt = document.getElementById("screenPrompt");
const screenResult = document.getElementById("screenResult");
const entityGrid = document.getElementById("entityGrid");
const errorBox = document.getElementById("errorBox");

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    promptInput.value = presets[chip.dataset.preset];
    promptInput.focus();
  });
});

function showError(message) {
  errorBox.textContent = message;
  errorBox.style.display = "block";
}

function clearError() {
  errorBox.style.display = "none";
  errorBox.textContent = "";
}

function runAssemblyAnimation() {
  return new Promise((resolve) => {
    assembly.classList.add("active");
    stages.forEach((s) => s.classList.remove("active", "done"));
    assemblyFill.style.width = "0%";

    const stageDurations = [400, 500, 500, 400];
    let elapsed = 0;
    stages.forEach((stageEl, i) => {
      setTimeout(() => {
        stages.forEach((s) => s.classList.remove("active"));
        stageEl.classList.add("active");
        assemblyFill.style.width = ((i + 0.5) / 4) * 100 + "%";
      }, elapsed);
      elapsed += stageDurations[i];
      setTimeout(() => {
        stageEl.classList.remove("active");
        stageEl.classList.add("done");
        assemblyFill.style.width = ((i + 1) / 4) * 100 + "%";
      }, elapsed);
    });

    setTimeout(resolve, elapsed + 200);
  });
}

async function forge() {
  const prompt = promptInput.value.trim();
  if (!prompt) {
    promptInput.focus();
    return;
  }

  clearError();
  forgeBtn.disabled = true;
  inputMode.style.display = "none";

  const startTime = performance.now();
  const animationPromise = runAssemblyAnimation();

  try {
    const res = await fetch(
      `${BASE_URL}/generate?prompt=${encodeURIComponent(prompt)}`,
      { method: "POST" }
    );

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || `Server responded ${res.status}`);
    }

    await animationPromise;
    const genTime = ((performance.now() - startTime) / 1000).toFixed(1);
    await showResult(data, genTime);
  } catch (err) {
    await animationPromise;
    assembly.classList.remove("active");
    inputMode.style.display = "block";
    forgeBtn.disabled = false;
    showError(`Generation failed: ${err.message}. Try again, this is sometimes a transient issue.`);
  }
}

async function showResult(data, genTime) {
  document.getElementById("docsUrlText").textContent = data.docs_url;
  document.getElementById("statEntities").textContent = data.entity_count;
  document.getElementById("statRoutes").textContent = data.route_count;
  document.getElementById("statTime").textContent = genTime + "s";

  const openDocsBtn = document.getElementById("openDocsBtn");
  openDocsBtn.href = BASE_URL + data.docs_url;

  const copyBtn = document.getElementById("copyBtn");
  copyBtn.dataset.baseUrl = BASE_URL + data.docs_url.replace("/docs", "");

  // Fetch the OpenAPI schema from the freshly mounted sub-app so we can
  // show the real detected entities/fields, and get an accurate seed
  // record count, rather than guessing.
  let recordCount = 0;
  entityGrid.innerHTML = "";
  try {
    const schemaRes = await fetch(BASE_URL + data.docs_url.replace("/docs", "/openapi.json"));
    const schema = await schemaRes.json();
    const paths = schema.paths || {};

    const entityNames = new Set();
    Object.values(paths).forEach((methods) => {
      Object.values(methods).forEach((op) => {
        if (op.summary && op.summary.toLowerCase().startsWith("list")) {
          entityNames.add(op.summary.replace(/list /i, "").trim());
        }
      });
    });

    for (const name of entityNames) {
      const listPath = Object.keys(paths).find((p) =>
        Object.values(paths[p]).some(
          (op) => op.summary && op.summary.toLowerCase() === `list ${name}`
        )
      );
      if (!listPath) continue;

      try {
        const recordsRes = await fetch(BASE_URL + data.docs_url.replace("/docs", "") + listPath);
        const records = await recordsRes.json();
        recordCount += Array.isArray(records) ? records.length : 0;

        const fields = Array.isArray(records) && records[0] ? Object.keys(records[0]) : [];
        const card = document.createElement("div");
        card.className = "entity-card";
        card.innerHTML = `<div class="entity-name">${name}</div>` +
          fields.map((f) => `<div class="field"><span>${f}</span></div>`).join("");
        entityGrid.appendChild(card);
      } catch (e) {
        // skip entity if its list endpoint fails, non-fatal
      }
    }
  } catch (e) {
    // schema introspection failed — not fatal, just skip the entity cards
  }

  document.getElementById("statRecords").textContent = recordCount;

  screenPrompt.style.display = "none";
  screenResult.classList.add("active");
}

forgeBtn.addEventListener("click", forge);
promptInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) forge();
});

document.getElementById("regenBtn").addEventListener("click", () => {
  screenResult.classList.remove("active");
  screenPrompt.style.display = "block";
  document.getElementById("inputMode").style.display = "block";
  assembly.classList.remove("active");
  forgeBtn.disabled = false;
  promptInput.value = "";
  clearError();
  promptInput.focus();
});

document.getElementById("copyBtn").addEventListener("click", (e) => {
  const btn = e.currentTarget;
  const url = btn.dataset.baseUrl || "";
  navigator.clipboard.writeText(url).catch(() => {});
  const original = btn.textContent;
  btn.textContent = "Copied";
  setTimeout(() => { btn.textContent = original; }, 1200);
});