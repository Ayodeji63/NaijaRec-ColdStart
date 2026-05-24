const persona = document.querySelector("#persona");
const domain = document.querySelector("#domain");
const city = document.querySelector("#city");
const topK = document.querySelector("#topK");
const statusEl = document.querySelector("#status");
const systemInfoEl = document.querySelector("#systemInfo");
const evidenceEl = document.querySelector("#evidence");
const resultsEl = document.querySelector("#results");
const recommendBtn = document.querySelector("#recommendBtn");
const benchmarkBtn = document.querySelector("#benchmarkBtn");
const personaMode = document.querySelector("#personaMode");
const benchmarkMode = document.querySelector("#benchmarkMode");
const personaControls = document.querySelector("#personaControls");
const benchmarkControls = document.querySelector("#benchmarkControls");
const benchmarkModel = document.querySelector("#benchmarkModel");
const benchmarkMethod = document.querySelector("#benchmarkMethod");
const benchmarkUser = document.querySelector("#benchmarkUser");
const benchmarkTopK = document.querySelector("#benchmarkTopK");

let models = {};
let mode = "persona";

const samples = {
  restaurant:
    "A Nigerian student in Philadelphia who enjoys spicy food, grilled meat, jollof-style rice dishes, suya-like flavours, large portions, and affordable casual restaurants.",
  grocery:
    "A health-conscious shopper who likes organic gluten-free snacks, spicy sauces, coffee, tea, and good-value pantry staples.",
};

function setLoading(isLoading, button) {
  button.disabled = isLoading;
  button.textContent = isLoading
    ? "Ranking..."
    : button === benchmarkBtn
      ? "Show Ranking"
      : "Recommend";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function clearEvidence() {
  evidenceEl.className = "hidden";
  evidenceEl.innerHTML = "";
}

function renderSystemInfo(entries) {
  systemInfoEl.innerHTML = entries
    .map(([name, value]) => `
      <div class="system-field">
        <span>${escapeHtml(name)}</span>
        <strong>${escapeHtml(value)}</strong>
      </div>
    `)
    .join("");
}

function renderPersonaSystemInfo() {
  renderSystemInfo([
    ["Mode", "New persona cold-start"],
    ["Retriever", "Metadata profile matching"],
    ["Reranker", "Not applied in live persona mode"],
    ["Top-K", String(Number(topK.value || 5))],
  ]);
}

function renderBenchmarkSystemInfo(body) {
  renderSystemInfo([
    ["Mode", "Evaluated model output"],
    ["Dataset", body.model_label],
    ["Method", body.method_label],
    ["Top-K", String(body.top_k)],
  ]);
}

function renderEvidence(body) {
  const metrics = Object.entries(body.reported_metrics || {})
    .map(([name, value]) => `<span class="metric">${escapeHtml(name.toUpperCase())}: ${Number(value).toFixed(4)}</span>`)
    .join("");
  evidenceEl.className = "evidence";
  evidenceEl.innerHTML = `
    <div class="evidence-title">${escapeHtml(body.method_label)}</div>
    <div class="evidence-keywords">Keyword evidence: ${escapeHtml((body.keywords || []).slice(0, 10).join(", "))}</div>
    <div class="metrics">${metrics}</div>
  `;
}

function renderResults(items) {
  if (!items.length) {
    resultsEl.innerHTML = '<div class="empty">No matching recommendations found.</div>';
    return;
  }
  resultsEl.innerHTML = items
    .map((item) => {
      const location = item.city ? `<div><span>Location:</span> ${escapeHtml(item.city)}</div>` : "";
      const categories = item.categories ? `<div><span>Categories:</span> ${escapeHtml(item.categories)}</div>` : "";
      const rating = item.metadata?.stars ? `<div><span>Rating:</span> ${escapeHtml(item.metadata.stars)} stars</div>` : "";
      const price = item.metadata?.price && item.metadata.price !== "?"
        ? `<div><span>Price:</span> ${escapeHtml(item.metadata.price)}</div>`
        : "";
      const signals = item.matched_signals?.length
        ? `<div class="signals"><span>Matched signals:</span> ${escapeHtml(item.matched_signals.join(", "))}</div>`
        : "";
      return `
        <article class="result">
          <div class="result-top">
            <div class="rank-name">
              <div class="rank">${escapeHtml(item.rank)}</div>
              <div>
                <div class="name">${escapeHtml(item.name)}</div>
              </div>
            </div>
            <div class="score" title="Recommendation relevance score">${escapeHtml(item.score)}</div>
          </div>
          <div class="meta">${location}${categories}${rating}${price}</div>
          ${signals}
          <div class="reason"><span>Why recommended:</span> ${escapeHtml(item.reason)}</div>
        </article>
      `;
    })
    .join("");
}

async function recommendPersona() {
  setLoading(true, recommendBtn);
  statusEl.textContent = "Ranking candidates";
  clearEvidence();
  renderPersonaSystemInfo();
  resultsEl.innerHTML = "";
  const selectedDomain = domain.value;
  try {
    const response = await fetch("/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        persona: persona.value,
        domain: selectedDomain,
        top_k: Number(topK.value || 5),
        city: selectedDomain === "restaurants" ? city.value || null : null,
      }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || "Recommendation failed");
    statusEl.textContent = `${body.count} recommendations for new persona`;
    renderResults(body.recommendations);
  } catch (error) {
    statusEl.textContent = "Error";
    resultsEl.innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
  } finally {
    setLoading(false, recommendBtn);
  }
}

async function loadModels() {
  if (Object.keys(models).length) return;
  const response = await fetch("/benchmark/models");
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail || "Could not load evaluated models");
  models = body;
  benchmarkModel.innerHTML = Object.entries(models)
    .map(([key, value]) => `<option value="${escapeHtml(key)}">${escapeHtml(value.label)}</option>`)
    .join("");
  await syncBenchmarkModel();
}

async function syncBenchmarkModel() {
  const model = models[benchmarkModel.value];
  benchmarkMethod.innerHTML = Object.entries(model.methods)
    .map(([key, value]) => `<option value="${escapeHtml(key)}">${escapeHtml(value.label)}</option>`)
    .join("");
  benchmarkMethod.value = model.default_method;
  const response = await fetch(`/benchmark/users/${encodeURIComponent(benchmarkModel.value)}?limit=30`);
  const users = await response.json();
  if (!response.ok) throw new Error(users.detail || "Could not load evaluation users");
  benchmarkUser.innerHTML = users
    .map((user) => `<option value="${escapeHtml(user.user_id)}">${escapeHtml(user.user_id)} | ${escapeHtml(user.keywords.slice(0, 3).join(", "))}</option>`)
    .join("");
}

async function recommendBenchmark() {
  setLoading(true, benchmarkBtn);
  statusEl.textContent = "Loading evaluated ranking";
  resultsEl.innerHTML = "";
  try {
    const response = await fetch("/benchmark/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: benchmarkModel.value,
        method: benchmarkMethod.value,
        user_id: benchmarkUser.value,
        top_k: Number(benchmarkTopK.value || 10),
      }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || "Evaluated ranking failed");
    statusEl.textContent = `${body.model_label} | ${body.user_id}`;
    renderBenchmarkSystemInfo(body);
    renderEvidence(body);
    renderResults(body.recommendations);
  } catch (error) {
    statusEl.textContent = "Error";
    clearEvidence();
    resultsEl.innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
  } finally {
    setLoading(false, benchmarkBtn);
  }
}

async function switchMode(nextMode) {
  mode = nextMode;
  const isPersona = mode === "persona";
  personaMode.classList.toggle("active", isPersona);
  benchmarkMode.classList.toggle("active", !isPersona);
  personaControls.classList.toggle("hidden", !isPersona);
  benchmarkControls.classList.toggle("hidden", isPersona);
  clearEvidence();
  if (isPersona) {
    await recommendPersona();
  } else {
    try {
      await loadModels();
      await recommendBenchmark();
    } catch (error) {
      statusEl.textContent = "Error";
      resultsEl.innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
    }
  }
}

function syncControls() {
  const isRestaurant = domain.value === "restaurants";
  if (isRestaurant && persona.value.trim() === samples.grocery) {
    persona.value = samples.restaurant;
  }
  if (!isRestaurant && persona.value.trim() === samples.restaurant) {
    persona.value = samples.grocery;
  }
  city.disabled = !isRestaurant;
  if (!isRestaurant) city.value = "";
  if (mode === "persona") renderPersonaSystemInfo();
}

recommendBtn.addEventListener("click", recommendPersona);
benchmarkBtn.addEventListener("click", recommendBenchmark);
personaMode.addEventListener("click", () => switchMode("persona"));
benchmarkMode.addEventListener("click", () => switchMode("benchmark"));
benchmarkModel.addEventListener("change", async () => {
  await syncBenchmarkModel();
  await recommendBenchmark();
});
benchmarkMethod.addEventListener("change", recommendBenchmark);
benchmarkUser.addEventListener("change", recommendBenchmark);
domain.addEventListener("change", syncControls);
document.querySelector("#sampleRestaurant").addEventListener("click", () => {
  domain.value = "restaurants";
  city.value = "Philadelphia";
  persona.value = samples.restaurant;
  syncControls();
});
document.querySelector("#sampleGrocery").addEventListener("click", () => {
  domain.value = "amazon_grocery_dense";
  persona.value = samples.grocery;
  syncControls();
});

syncControls();
recommendPersona();
