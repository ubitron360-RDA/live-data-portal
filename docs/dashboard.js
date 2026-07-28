const SERIES_COLORS = [
  "--series-1", "--series-2", "--series-3", "--series-4", "--series-5", "--series-6",
];

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

async function loadJSON(path) {
  try {
    const res = await fetch(path, { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.warn(`failed to load ${path}`, err);
    return null;
  }
}

function formatValue(value, unit) {
  if (value === null || value === undefined) return "-";
  const decimals = Math.abs(value) < 10 ? 2 : Math.abs(value) < 1000 ? 2 : 0;
  return `${value.toLocaleString(undefined, { maximumFractionDigits: decimals })}`;
}

function renderPriceCard(series) {
  const card = document.createElement("div");
  card.className = "price-card";

  const changeClass = series.change_pct > 0 ? "up" : series.change_pct < 0 ? "down" : "flat";
  const changeSign = series.change_pct > 0 ? "+" : "";

  card.innerHTML = `
    <div class="name">${series.name}</div>
    <div class="value-row">
      <span class="value">${formatValue(series.latest_value)}</span>
      <span class="unit">${series.unit}</span>
    </div>
    <div class="change ${changeClass}">
      ${series.change_pct === null ? "no prior value" : `${changeSign}${series.change_pct}%`}
    </div>
    <div class="as-of">as of ${series.latest_date} &middot; ${series.source.toUpperCase()}</div>
  `;

  return card;
}

function renderChartCard(series, colorVar) {
  const card = document.createElement("div");
  card.className = "chart-card";
  card.innerHTML = `
    <div class="chart-header">
      <span class="series-name">${series.name}</span>
      <span class="series-meta">${series.unit} &middot; as of ${series.latest_date}</span>
    </div>
    <div class="chart-wrap"><canvas></canvas></div>
  `;

  const canvas = card.querySelector("canvas");
  const history = series.history || [];
  new Chart(canvas, {
    type: "line",
    data: {
      labels: history.map((h) => h.date),
      datasets: [{
        data: history.map((h) => h.value),
        borderColor: cssVar(colorVar),
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.15,
        fill: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        x: { display: true, ticks: { color: cssVar("--text-muted"), maxTicksLimit: 6 }, grid: { color: cssVar("--gridline") } },
        y: { display: true, ticks: { color: cssVar("--text-muted") }, grid: { color: cssVar("--gridline") } },
      },
      plugins: { legend: { display: false }, tooltip: { enabled: true } },
    },
  });

  return card;
}

function renderFlowPanel(title, rows, unit, extraClass) {
  const panel = document.createElement("div");
  panel.className = `flow-panel ${extraClass}`;
  const maxValue = rows.length ? Math.max(...rows.map((r) => r.value)) : 1;

  const rowsHtml = rows.map((r) => `
    <tr>
      <td>${r.country}
        <div class="bar-track"><div class="bar-fill" style="width:${(r.value / maxValue) * 100}%"></div></div>
      </td>
      <td>${formatValue(r.value)} ${unit}</td>
    </tr>
  `).join("");

  panel.innerHTML = `
    <h3>${title}</h3>
    <table class="flow-table">
      <thead><tr><th>Country</th><th>Volume</th></tr></thead>
      <tbody>${rowsHtml || `<tr><td colspan="2">No data yet</td></tr>`}</tbody>
    </table>
  `;
  return panel;
}

async function main() {
  const [prices, flows, meta] = await Promise.all([
    loadJSON("data/processed/prices.json"),
    loadJSON("data/processed/flows.json"),
    loadJSON("data/processed/meta.json"),
  ]);

  // --- prices ---
  const priceGrid = document.getElementById("priceGrid");
  const chartStack = document.getElementById("chartStack");
  const series = prices?.series || [];
  if (series.length === 0) {
    const emptyMsg = `<div class="empty-state">No price data yet. Run the ingestion pipeline (see README) with FRED_API_KEY / EIA_API_KEY set to populate this dashboard.</div>`;
    priceGrid.innerHTML = emptyMsg;
    chartStack.innerHTML = emptyMsg;
  } else {
    series.forEach((s, i) => {
      priceGrid.appendChild(renderPriceCard(s));
      chartStack.appendChild(renderChartCard(s, SERIES_COLORS[i % SERIES_COLORS.length]));
    });
  }

  // --- flows ---
  const flowsGrid = document.getElementById("flowsGrid");
  const jodi = flows?.jodi;
  if (!jodi) {
    flowsGrid.innerHTML = `<div class="empty-state">No flow data yet. Run <code>ingestion/jodi.py</code> and the transform scripts to populate this section.</div>`;
  } else {
    flowsGrid.appendChild(renderFlowPanel("Top Exporters", jodi.top_exporters, jodi.unit, "exporters"));
    flowsGrid.appendChild(renderFlowPanel("Top Importers", jodi.top_importers, jodi.unit, "importers"));
  }

  // --- meta / footer ---
  const footer = document.getElementById("metaFooter");
  if (meta) {
    const rows = Object.entries(meta.sources || {})
      .map(([src, info]) => `<tr><td>${src.toUpperCase()}</td><td>${info.available ? `last updated ${info.last_updated}` : "no data"}</td></tr>`)
      .join("");
    footer.innerHTML = `Pipeline last ran ${meta.generated_at ? new Date(meta.generated_at).toLocaleString() : "-"}<table>${rows}</table>`;
  }

  document.getElementById("generatedAt").textContent = meta?.generated_at
    ? `Data last refreshed ${new Date(meta.generated_at).toLocaleString()}`
    : "";
}

// --- theme toggle ---
const themeToggle = document.getElementById("themeToggle");
function applyStoredTheme() {
  const stored = localStorage.getItem("theme");
  if (stored) document.documentElement.setAttribute("data-theme", stored);
}
themeToggle.addEventListener("click", () => {
  const current = document.documentElement.getAttribute("data-theme") ||
    (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
});
applyStoredTheme();

main();
