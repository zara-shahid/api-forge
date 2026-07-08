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
const erDiagram = document.getElementById("erDiagram");
const errorBox = document.getElementById("errorBox");
const toast = document.getElementById("toast");

const historyToggle = document.getElementById("historyToggle");
const historyDrawer = document.getElementById("historyDrawer");
const historyBackdrop = document.getElementById("historyBackdrop");
const historyClose = document.getElementById("historyClose");
const historyList = document.getElementById("historyList");
const historyCount = document.getElementById("historyCount");

const pgEntity = document.getElementById("pgEntity");
const pgOperation = document.getElementById("pgOperation");
const pgIdField = document.getElementById("pgIdField");
const pgId = document.getElementById("pgId");
const pgSend = document.getElementById("pgSend");
const pgMethod = document.getElementById("pgMethod");
const pgUrl = document.getElementById("pgUrl");
const pgCurl = document.getElementById("pgCurl");
const pgBodyWrap = document.getElementById("pgBodyWrap");
const pgBody = document.getElementById("pgBody");
const pgStatus = document.getElementById("pgStatus");
const pgTime = document.getElementById("pgTime");
const pgResponseBody = document.getElementById("pgResponseBody");

let currentApi = null;
let playgroundOps = [];

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    promptInput.value = presets[chip.dataset.preset];
    promptInput.focus();
  });
});

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2200);
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.style.display = "block";
}

function clearError() {
  errorBox.style.display = "none";
  errorBox.textContent = "";
}

function switchResultScreen(screenName) {
  document.querySelectorAll(".nav-link").forEach((link) => {
    link.classList.toggle("active", link.dataset.screen === screenName);
  });
  document.querySelectorAll(".result-screen").forEach((screen) => {
    const id = screen.id.replace("screen", "").toLowerCase();
    screen.classList.toggle("active", id === screenName);
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

document.querySelectorAll(".nav-link").forEach((link) => {
  link.addEventListener("click", () => switchResultScreen(link.dataset.screen));
});

function showAppShell() {
  document.body.classList.add("in-app");
  switchResultScreen("overview");
}

function hideAppShell() {
  document.body.classList.remove("in-app");
}

function openHistory() {
  historyDrawer.classList.add("open");
  historyBackdrop.classList.add("open");
}

function closeHistory() {
  historyDrawer.classList.remove("open");
  historyBackdrop.classList.remove("open");
}

historyToggle.addEventListener("click", openHistory);
historyClose.addEventListener("click", closeHistory);
historyBackdrop.addEventListener("click", closeHistory);

async function refreshHistory(activeId) {
  try {
    const res = await fetch(`${BASE_URL}/apis`);
    const apis = await res.json();
    historyCount.textContent = apis.length;

    if (apis.length === 0) {
      historyList.innerHTML = '<div class="history-empty">No APIs forged yet.<br>Generate one to get started.</div>';
      return;
    }

    historyList.innerHTML = "";
    apis.reverse().forEach((api) => {
      const btn = document.createElement("button");
      btn.className = "history-item" + (api.api_id === activeId ? " active" : "");
      btn.innerHTML =
        `<div class="history-item-title">${escapeHtml(api.title)}</div>` +
        `<div class="history-item-meta">${api.entity_count} entities · ${api.route_count} routes · ${api.api_id.slice(0, 8)}…</div>`;
      btn.addEventListener("click", () => loadFromHistory(api.api_id));
      historyList.appendChild(btn);
    });
  } catch (e) {
    historyCount.textContent = "0";
  }
}

async function loadFromHistory(apiId) {
  try {
    const res = await fetch(`${BASE_URL}/apis/${apiId}`);
    if (!res.ok) throw new Error("API not found");
    const data = await res.json();
    closeHistory();
    await showResult(data, "—", false);
    showToast("Loaded from session history");
  } catch (e) {
    showToast("Could not load API — it may have been cleared on restart");
  }
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function renderErDiagram(entities) {
  if (!entities || entities.length === 0) {
    erDiagram.className = "er-diagram empty";
    erDiagram.textContent = "No entity relationships detected.";
    return;
  }

  erDiagram.className = "er-diagram";
  erDiagram.innerHTML = "";

  const relations = [];
  entities.forEach((e) => {
    (e.relationships || []).forEach((rel) => {
      relations.push(`${e.name} → ${rel}`);
    });
  });

  entities.forEach((e, i) => {
    const node = document.createElement("div");
    node.className = "er-node";
    node.style.animationDelay = `${i * 0.06}s`;
    const fieldNames = (e.fields || []).slice(0, 4).map((f) => f.name).join(", ");
    const more = (e.fields || []).length > 4 ? ` +${e.fields.length - 4}` : "";
    node.innerHTML =
      `<div class="er-node-name">${escapeHtml(e.name)}</div>` +
      `<div class="er-node-fields">${escapeHtml(fieldNames)}${more}</div>`;
    erDiagram.appendChild(node);
  });

  if (relations.length > 0) {
    const relWrap = document.createElement("div");
    relWrap.className = "er-relations";
    relations.forEach((r) => {
      const tag = document.createElement("span");
      tag.className = "er-relation";
      tag.textContent = r;
      relWrap.appendChild(tag);
    });
    erDiagram.appendChild(relWrap);
  }
}

function buildPlaygroundOps(basePath, paths) {
  const ops = [];
  Object.entries(paths).forEach(([path, methods]) => {
    Object.entries(methods).forEach(([method, op]) => {
      if (!op.summary) return;
      const summary = op.summary.toLowerCase();
      let behavior = "other";
      if (summary.startsWith("list ")) behavior = "list";
      else if (summary.startsWith("get one ")) behavior = "get_one";
      else if (summary.startsWith("create ")) behavior = "create";
      else if (summary.startsWith("update ")) behavior = "update";
      else if (summary.startsWith("delete ")) behavior = "delete";

      const entity = op.summary.replace(/^(list|get one|create|update|delete)\s/i, "").trim();
      ops.push({
        entity,
        behavior,
        method: method.toUpperCase(),
        path,
        label: op.summary,
      });
    });
  });
  return ops.sort((a, b) => a.entity.localeCompare(b.entity) || a.method.localeCompare(b.method));
}

function populatePlayground(basePath, paths, sampleRecords) {
  playgroundOps = buildPlaygroundOps(basePath, paths);

  const entities = [...new Set(playgroundOps.map((o) => o.entity))];
  pgEntity.innerHTML = entities.map((e) => `<option value="${escapeHtml(e)}">${escapeHtml(e)}</option>`).join("");

  pgEntity.onchange = updatePlaygroundOps;
  pgOperation.onchange = updatePlaygroundUI;
  updatePlaygroundOps();

  currentApi.sampleRecords = sampleRecords;
}

function updatePlaygroundOps() {
  const entity = pgEntity.value;
  const ops = playgroundOps.filter((o) => o.entity === entity);
  pgOperation.innerHTML = ops.map((o, i) =>
    `<option value="${i}">${escapeHtml(o.label)}</option>`
  ).join("");
  updatePlaygroundUI();
}

function updatePlaygroundUI() {
  const entity = pgEntity.value;
  const ops = playgroundOps.filter((o) => o.entity === entity);
  const op = ops[parseInt(pgOperation.value, 10)];
  if (!op) return;

  pgMethod.textContent = op.method;
  pgMethod.className = "pg-method " + op.method.toLowerCase();

  const needsId = op.path.includes("{id}");
  pgIdField.style.display = needsId ? "block" : "none";

  const needsBody = op.method === "POST" || op.method === "PUT";
  pgBodyWrap.style.display = needsBody ? "block" : "none";

  if (needsBody && currentApi?.sampleRecords?.[entity]?.[0]) {
    const sample = { ...currentApi.sampleRecords[entity][0] };
    delete sample.id;
    pgBody.value = JSON.stringify(sample, null, 2);
  } else if (needsBody) {
    pgBody.value = "{}";
  }

  let displayPath = currentApi.basePath + op.path;
  if (needsId && pgId.value) {
    displayPath = displayPath.replace("{id}", pgId.value);
  } else if (needsId) {
    displayPath = displayPath.replace("{id}", "1");
  }
  pgUrl.textContent = displayPath;
}

pgId.addEventListener("input", updatePlaygroundUI);

async function sendPlaygroundRequest() {
  const entity = pgEntity.value;
  const ops = playgroundOps.filter((o) => o.entity === entity);
  const op = ops[parseInt(pgOperation.value, 10)];
  if (!op || !currentApi) return;

  let url = BASE_URL + currentApi.basePath + op.path;
  if (op.path.includes("{id}")) {
    const id = pgId.value.trim() || "1";
    url = url.replace("{id}", id);
  }

  pgStatus.textContent = "Sending…";
  pgStatus.className = "pg-status pending";
  pgTime.textContent = "";
  pgResponseBody.textContent = "Waiting for response…";
  pgResponseBody.classList.remove("has-data");

  const start = performance.now();
  const opts = { method: op.method, headers: {} };

  if (op.method === "POST" || op.method === "PUT") {
    opts.headers["Content-Type"] = "application/json";
    try {
      opts.body = JSON.stringify(JSON.parse(pgBody.value));
    } catch (e) {
      pgStatus.textContent = "Invalid JSON";
      pgStatus.className = "pg-status err";
      pgResponseBody.textContent = "Fix the request body — it must be valid JSON.";
      return;
    }
  }

  try {
    const res = await fetch(url, opts);
    const elapsed = ((performance.now() - start) / 1000).toFixed(2);
    pgTime.textContent = `${elapsed}s · ${res.status} ${res.statusText}`;

    let body;
    const text = await res.text();
    try { body = JSON.stringify(JSON.parse(text), null, 2); } catch { body = text; }

    pgStatus.textContent = res.ok ? `${res.status} OK` : `${res.status} Error`;
    pgStatus.className = "pg-status " + (res.ok ? "ok" : "err");
    pgResponseBody.textContent = body || "(empty response)";
    pgResponseBody.classList.add("has-data");
  } catch (err) {
    pgStatus.textContent = "Failed";
    pgStatus.className = "pg-status err";
    pgResponseBody.textContent = err.message;
  }
}

function buildCurlCommand() {
  const entity = pgEntity.value;
  const ops = playgroundOps.filter((o) => o.entity === entity);
  const op = ops[parseInt(pgOperation.value, 10)];
  if (!op || !currentApi) return "";

  let url = BASE_URL + currentApi.basePath + op.path;
  if (op.path.includes("{id}")) {
    url = url.replace("{id}", pgId.value.trim() || "1");
  }

  let cmd = `curl -X ${op.method} "${url}"`;
  if (op.method === "POST" || op.method === "PUT") {
    cmd += ` \\\n  -H "Content-Type: application/json" \\\n  -d '${pgBody.value.replace(/\n/g, "").replace(/'/g, "'\\''")}'`;
  }
  return cmd;
}

pgSend.addEventListener("click", sendPlaygroundRequest);
pgCurl.addEventListener("click", () => {
  navigator.clipboard.writeText(buildCurlCommand()).catch(() => {});
  showToast("cURL command copied");
});

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
    await showResult(data, genTime, true);
  } catch (err) {
    await animationPromise;
    assembly.classList.remove("active");
    inputMode.style.display = "block";
    forgeBtn.disabled = false;
    showError(`Generation failed: ${err.message}. Try again, this is sometimes a transient issue.`);
  }
}

async function showResult(data, genTime, fromForge) {
  document.getElementById("docsUrlText").textContent = data.docs_url;
  document.getElementById("statEntities").textContent = data.entity_count;
  document.getElementById("statRoutes").textContent = data.route_count;
  document.getElementById("statTime").textContent = genTime + "s";

  const basePath = data.docs_url.replace("/docs", "");
  currentApi = {
    api_id: data.api_id,
    basePath,
    docs_url: data.docs_url,
    entities: data.entities || [],
  };

  const openDocsBtn = document.getElementById("openDocsBtn");
  openDocsBtn.href = BASE_URL + data.docs_url;

  const copyBtn = document.getElementById("copyBtn");
  copyBtn.dataset.baseUrl = BASE_URL + basePath;

  const exportBtn = document.getElementById("exportBtn");
  exportBtn.dataset.openapiUrl = BASE_URL + basePath + "/openapi.json";
  exportBtn.dataset.apiId = data.api_id;

  renderErDiagram(data.entities || []);

  let recordCount = 0;
  const sampleRecords = {};
  entityGrid.innerHTML = "";

  try {
    const schemaRes = await fetch(BASE_URL + basePath + "/openapi.json");
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

    let cardIndex = 0;
    for (const name of entityNames) {
      const listPath = Object.keys(paths).find((p) =>
        Object.values(paths[p]).some(
          (op) => op.summary && op.summary.toLowerCase() === `list ${name}`
        )
      );
      if (!listPath) continue;

      try {
        const recordsRes = await fetch(BASE_URL + basePath + listPath);
        const records = await recordsRes.json();
        if (Array.isArray(records)) {
          recordCount += records.length;
          sampleRecords[name] = records;
        }

        const entityMeta = (data.entities || []).find((e) => e.name === name);
        const fields = entityMeta
          ? entityMeta.fields.map((f) => f.name)
          : (Array.isArray(records) && records[0] ? Object.keys(records[0]) : []);

        const card = document.createElement("div");
        card.className = "entity-card";
        card.style.animationDelay = `${cardIndex * 0.08}s`;
        card.innerHTML = `<div class="entity-name">${escapeHtml(name)}</div>` +
          fields.map((f) => {
            const spec = entityMeta?.fields?.find((ef) => ef.name === f);
            const req = spec?.required ? '<span class="req">required</span>' : "";
            return `<div class="field"><span>${escapeHtml(f)}</span>${req}</div>`;
          }).join("");
        entityGrid.appendChild(card);
        cardIndex++;
      } catch (e) {
        // skip entity if its list endpoint fails
      }
    }

    populatePlayground(basePath, paths, sampleRecords);
  } catch (e) {
    pgResponseBody.textContent = "Could not load OpenAPI spec for playground.";
  }

  document.getElementById("statRecords").textContent = recordCount;

  screenPrompt.style.display = "none";
  screenResult.classList.add("active");
  showAppShell();
  window.scrollTo({ top: 0, behavior: "smooth" });
  window.Forge3D?.hide();

  refreshHistory(data.api_id);

  if (fromForge) {
    forgeBtn.disabled = false;
  }
}

forgeBtn.addEventListener("click", forge);
promptInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) forge();
});

document.getElementById("regenBtn").addEventListener("click", () => {
  screenResult.classList.remove("active");
  hideAppShell();
  screenPrompt.style.display = "block";
  document.getElementById("inputMode").style.display = "block";
  assembly.classList.remove("active");
  forgeBtn.disabled = false;
  promptInput.value = "";
  clearError();
  currentApi = null;
  promptInput.focus();
  window.scrollTo({ top: 0, behavior: "smooth" });
  window.Forge3D?.show();
});

document.getElementById("copyBtn").addEventListener("click", () => {
  const url = document.getElementById("copyBtn").dataset.baseUrl || "";
  navigator.clipboard.writeText(url).catch(() => {});
  showToast("Base URL copied to clipboard");
});

document.getElementById("exportBtn").addEventListener("click", async () => {
  const btn = document.getElementById("exportBtn");
  const url = btn.dataset.openapiUrl;
  const apiId = btn.dataset.apiId || "api";
  if (!url) return;

  try {
    const res = await fetch(url);
    const spec = await res.json();
    const blob = new Blob([JSON.stringify(spec, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `api-forge-${apiId.slice(0, 8)}.openapi.json`;
    a.click();
    URL.revokeObjectURL(a.href);
    showToast("OpenAPI spec downloaded");
  } catch (e) {
    showToast("Export failed — try again");
  }
});

refreshHistory(null);
