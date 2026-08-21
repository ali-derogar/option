/**
 * TSETMC Options Dashboard — frontend
 */

const underlyingMatch = window.location.pathname.match(/^\/underlying\/(.+)$/);
const initialParams = new URLSearchParams(window.location.search);

const state = {
  view: underlyingMatch ? "underlying" : "underlyings",
  underlyingKey: underlyingMatch ? decodeURIComponent(underlyingMatch[1]) : null,
  selectedDate: initialParams.get("date") || "",
  availableDates: [],
  items: [],
  filtered: [],
  sortKey: null,
  sortDir: 1,
  selectedInsCode: null,
  selectedRowKey: null,
  oiChart: null,
  underlying: null,
  analysisVisible: false,
  trendRequestId: 0,
  filters: {
    type: "all",
    expiry: "all",
    moneyness: "all",
    strikeMin: "",
    strikeMax: "",
  },
};

const VIEW_CONFIG = {
  underlyings: {
    title: "سهم‌های اصلی",
    searchPlaceholder: "جستجو سهم...",
    columns: [
      { key: "underlying_symbol", label: "سهم" },
      { key: "underlying_short_name", label: "نام" },
      { key: "contract_count", label: "قرارداد", fmt: "num" },
      { key: "call_count", label: "خرید", fmt: "num" },
      { key: "put_count", label: "فروش", fmt: "num" },
      { key: "nearest_end_date", label: "نزدیک‌ترین سررسید", fmt: "date" },
      { key: "min_strike_price", label: "کمترین اعمال", fmt: "num" },
      { key: "max_strike_price", label: "بیشترین اعمال", fmt: "num" },
      { key: "trade_volume", label: "حجم", fmt: "num" },
      { key: "trade_value", label: "ارزش", fmt: "num" },
    ],
  },
  underlying: {
    title: "قراردادهای اختیار معامله",
    searchPlaceholder: "جستجو قرارداد...",
    columns: [
      { key: "option_type", label: "نوع", fmt: "optionType" },
      { key: "symbol", label: "نماد قرارداد" },
      { key: "short_name", label: "نام" },
      { key: "strike_price", label: "اعمال", fmt: "num" },
      { key: "end_date", label: "سررسید", fmt: "date" },
      { key: "moneyness", label: "وضعیت" },
      { key: "last_price", label: "آخرین", fmt: "num" },
      { key: "closing_price", label: "پایانی", fmt: "num" },
      { key: "trade_volume", label: "حجم", fmt: "num" },
      { key: "buy_open_positions", label: "موقعیت باز", fmt: "num" },
    ],
  },
};

const DETAIL_LABELS = {
  ins_code: "کد نماد",
  symbol: "نماد",
  short_name: "نام کوتاه",
  long_name: "نام کامل",
  strike_price: "قیمت اعمال",
  end_date: "سررسید",
  contract_size: "اندازه قرارداد",
  underlying_symbol: "دارایی پایه",
  underlying_short_name: "نام دارایی پایه",
  underlying_ins_code: "کد دارایی پایه",
  underlying_last_price: "آخرین قیمت دارایی پایه",
  underlying_closing_price: "قیمت پایانی دارایی پایه",
  last_price: "آخرین قیمت",
  closing_price: "قیمت پایانی",
  price_change: "تغییر قیمت",
  trade_volume: "حجم معاملات",
  trade_value: "ارزش معاملات",
  buy_open_positions: "موقعیت باز",
  sell_open_positions: "موقعیت فروش",
  yesterday_open_positions: "موقعیت دیروز",
  natural_money_flow: "جریان پول حقیقی",
  legal_money_flow: "جریان پول حقوقی",
  natural_buy_count: "تعداد خریدار حقیقی",
  natural_buy_value: "ارزش خرید حقیقی",
  natural_sell_count: "تعداد فروشنده حقیقی",
  natural_sell_value: "ارزش فروش حقیقی",
  legal_buy_count: "تعداد خریدار حقوقی",
  legal_buy_value: "ارزش خرید حقوقی",
  legal_sell_count: "تعداد فروشنده حقوقی",
  legal_sell_value: "ارزش فروش حقوقی",
  option_type: "نوع قرارداد",
  moneyness: "وضعیت ITM/OTM",
  intrinsic_value: "ارزش ذاتی",
  market_name: "بازار",
  sector: "صنعت",
};

function fmtNum(n) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  return Number(n).toLocaleString("fa-IR", { maximumFractionDigits: 0 });
}

function fmtDate(d) {
  if (!d) return "—";
  const s = String(d);
  if (s.length === 8 && /^\d+$/.test(s)) {
    return `${s.slice(0, 4)}/${s.slice(4, 6)}/${s.slice(6, 8)}`;
  }
  try {
    return new Date(d).toLocaleString("fa-IR", { dateStyle: "short", timeStyle: "short" });
  } catch {
    return s;
  }
}

function fmtFlow(n) {
  if (n == null) return "—";
  const formatted = fmtNum(n);
  return n > 0 ? `+${formatted}` : formatted;
}

function fmtPct(n, multiplier = 100) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  return `${(Number(n) * multiplier).toLocaleString("fa-IR", { maximumFractionDigits: 1 })}٪`;
}

function fmtRatio(n) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  return Number(n).toLocaleString("fa-IR", { maximumFractionDigits: 2 });
}

function optionTypeLabel(value) {
  if (value === "call") return "خرید";
  if (value === "put") return "فروش";
  return "—";
}

function formatCell(col, val) {
  if (col.fmt === "num") return fmtNum(val);
  if (col.fmt === "date") return fmtDate(val);
  if (col.fmt === "flow") return fmtFlow(val);
  if (col.fmt === "pct") return fmtPct(val);
  if (col.fmt === "pct0") return fmtPct(val, 1);
  if (col.fmt === "ratio") return fmtRatio(val);
  if (col.fmt === "optionType") return optionTypeLabel(val);
  return val ?? "—";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function optionTypeClass(value) {
  if (value === "call") return "type-call";
  if (value === "put") return "type-put";
  return "type-unknown";
}

function showToast(msg, type = "success") {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = `toast ${type}`;
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => el.classList.add("hidden"), 3500);
}

function setLoading(on) {
  document.getElementById("loadingOverlay").classList.toggle("hidden", !on);
}

function setStatusText(text) {
  if (text) document.getElementById("lastUpdate").textContent = text;
}

function dateQuery(prefix = "?") {
  return state.selectedDate ? `${prefix}date=${encodeURIComponent(state.selectedDate)}` : "";
}

function appendQuery(params) {
  const query = new URLSearchParams();
  if (state.selectedDate) query.set("date", state.selectedDate);
  Object.entries(params).forEach(([key, value]) => {
    if (value) query.set(key, value);
  });
  const s = query.toString();
  return s ? `?${s}` : "";
}

function syncDateToUrl() {
  const url = new URL(window.location.href);
  if (state.selectedDate) url.searchParams.set("date", state.selectedDate);
  else url.searchParams.delete("date");
  window.history.replaceState({}, "", `${url.pathname}${url.search}`);
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || res.statusText);
  }
  return res.json();
}

async function loadSummary() {
  const s = await api(`/api/summary${dateQuery()}`);
  document.getElementById("statContracts").textContent = fmtNum(s.underlying_count);
  document.getElementById("statBuyOi").textContent = fmtNum(s.contract_count);
  document.getElementById("statSellOi").textContent = fmtNum(s.call_count);
  document.getElementById("statNaturalFlow").textContent = fmtNum(s.put_count);
  document.getElementById("statLegalFlow").textContent = fmtNum(s.total_trade_volume);
  document.getElementById("lastUpdate").textContent = s.last_update
    ? `تاریخ داده: ${state.selectedDate ? fmtDate(state.selectedDate) : "آخرین"} · بروزرسانی: ${fmtDate(s.last_update)}`
    : "بدون داده";
}

async function loadDates() {
  const input = document.getElementById("dateFilter");
  const options = document.getElementById("availableDates");
  const data = await api("/api/dates");
  state.availableDates = data.items || [];
  if (!state.selectedDate && data.latest) {
    state.selectedDate = data.latest;
  }
  options.innerHTML = state.availableDates.length
    ? state.availableDates
        .map((date) => `<option value="${escapeHtml(date)}">${escapeHtml(fmtDate(date))}</option>`)
        .join("")
    : "";
  input.value = state.selectedDate || "";
  syncDateToUrl();
}

function currentSearch() {
  return document.getElementById("searchInput").value.trim();
}

async function loadUnderlyings(search = "") {
  const q = appendQuery({ q: search });
  const data = await api(`/api/underlyings${q}`);
  state.items = data.items || [];
  applyFilterAndSort();
}

async function loadUnderlyingContracts(search = "") {
  const q = appendQuery({ q: search });
  const data = await api(`/api/underlyings/${encodeURIComponent(state.underlyingKey)}/contracts${q}`);
  state.items = data.items || [];
  state.underlying = data.underlying || null;
  populateExpiryFilter();
  applyFilterAndSort();
}

async function reloadActiveData() {
  if (state.view === "underlying") {
    await loadUnderlyingContracts(currentSearch());
  } else {
    await loadUnderlyings(currentSearch());
  }
}

function getRowKey(row) {
  if (!row) return "";
  if (state.view === "underlyings") return row.underlying_key ?? "";
  return row.row_key ?? row.ins_code ?? "";
}

function applyLocalFilters(items) {
  if (state.view !== "underlying") return [...items];
  const strikeMin = state.filters.strikeMin === "" ? null : Number(state.filters.strikeMin);
  const strikeMax = state.filters.strikeMax === "" ? null : Number(state.filters.strikeMax);

  return items.filter((row) => {
    if (state.filters.type !== "all" && row.option_type !== state.filters.type) return false;
    if (state.filters.expiry !== "all" && String(row.end_date) !== state.filters.expiry) return false;
    if (state.filters.moneyness !== "all" && row.moneyness !== state.filters.moneyness) return false;
    if (strikeMin != null && Number(row.strike_price) < strikeMin) return false;
    if (strikeMax != null && Number(row.strike_price) > strikeMax) return false;
    return true;
  });
}

function applyFilterAndSort() {
  state.filtered = applyLocalFilters(state.items);
  if (state.sortKey) {
    const key = state.sortKey;
    const dir = state.sortDir;
    state.filtered.sort((a, b) => {
      const av = a[key];
      const bv = b[key];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === "number" && typeof bv === "number") return (av - bv) * dir;
      return String(av).localeCompare(String(bv), "fa") * dir;
    });
  }
  renderTable();
  renderAnalysis();
}

function updateViewChrome() {
  const config = VIEW_CONFIG[state.view];
  document.getElementById("searchInput").placeholder = config.searchPlaceholder;
  document.getElementById("optionFilters").classList.toggle("hidden", state.view !== "underlying");
  document.getElementById("btnBack").classList.toggle("hidden", state.view !== "underlying");
  document.getElementById("detailPanel").classList.toggle("hidden", state.view !== "underlying");
  document.getElementById("analysisPanel").classList.toggle("hidden", state.view !== "underlying" || !state.analysisVisible);
  document.getElementById("btnAnalysis").classList.toggle("active", state.analysisVisible);
  document.querySelector(".main-grid").classList.toggle("no-detail", state.view !== "underlying");
  document.getElementById("detailTitle").textContent = "جزئیات قرارداد";
}

function renderTable() {
  const config = VIEW_CONFIG[state.view];
  const head = document.getElementById("tableHead");
  const body = document.getElementById("tableBody");
  const empty = document.getElementById("emptyState");
  const wrap = document.getElementById("tableWrap");
  const count = document.getElementById("rowCount");
  const title = document.getElementById("panelTitle");

  updateViewChrome();
  const underlyingName = state.underlying?.underlying_symbol || state.underlying?.underlying_short_name;
  title.textContent = state.view === "underlying" && underlyingName
    ? `${config.title} ${underlyingName}`
    : config.title;
  count.textContent = `${state.filtered.length} ردیف`;

  if (!state.filtered.length) {
    wrap.classList.add("hidden");
    empty.classList.remove("hidden");
    head.innerHTML = "";
    body.innerHTML = "";
    return;
  }

  wrap.classList.remove("hidden");
  empty.classList.add("hidden");

  head.innerHTML = `<tr>${config.columns
    .map(
      (c) =>
        `<th data-key="${escapeHtml(c.key)}" class="${state.sortKey === c.key ? "sorted" : ""}">${escapeHtml(c.label)}</th>`
    )
    .join("")}</tr>`;

  body.innerHTML = state.filtered
    .map((row, index) => {
      const selected = getRowKey(row) === state.selectedRowKey ? "selected" : "";
      const cells = config.columns
        .map((c) => {
          const val = row[c.key];
          let cls = "";
          if (c.fmt === "flow" && val != null) {
            cls = val > 0 ? "cell-positive" : val < 0 ? "cell-negative" : "";
          }
          if (c.fmt === "optionType") {
            cls = `type-badge ${optionTypeClass(row.option_type)}`;
          }
          return `<td><span class="${cls}">${escapeHtml(formatCell(c, val))}</span></td>`;
        })
        .join("");
      return `<tr data-index="${index}" class="${selected}">${cells}</tr>`;
    })
    .join("");

  head.querySelectorAll("th").forEach((th) => {
    th.addEventListener("click", () => {
      const key = th.dataset.key;
      if (state.sortKey === key) state.sortDir *= -1;
      else {
        state.sortKey = key;
        state.sortDir = 1;
      }
      applyFilterAndSort();
    });
  });

  body.querySelectorAll("tr").forEach((tr) => {
    tr.addEventListener("click", () => {
      selectRowByIndex(Number(tr.dataset.index));
    });
  });
}

function selectRowByIndex(index) {
  const row = state.filtered[index];
  if (!row) return;

  if (state.view === "underlyings") {
    const q = dateQuery();
    window.open(`/underlying/${encodeURIComponent(row.underlying_key)}${q}`, "_blank", "noopener");
    return;
  }

  state.selectedRowKey = getRowKey(row);
  state.selectedInsCode = row?.ins_code ?? null;
  renderTable();
  renderDetail(row);
  if (state.selectedInsCode) {
    loadOiChart(state.selectedInsCode);
  } else {
    document.getElementById("chartBlock").classList.add("hidden");
  }
}

function renderDetail(row) {
  const container = document.getElementById("detailContent");
  if (!row) {
    container.innerHTML = '<p class="detail-placeholder">یک ردیف از جدول را انتخاب کنید</p>';
    document.getElementById("chartBlock").classList.add("hidden");
    return;
  }

  const sections = [
    ["اطلاعات قرارداد", ["option_type", "symbol", "short_name", "long_name", "ins_code", "strike_price", "end_date", "contract_size", "moneyness", "intrinsic_value"]],
    ["دارایی پایه", ["underlying_symbol", "underlying_short_name", "underlying_ins_code", "underlying_last_price", "underlying_closing_price"]],
    ["معاملات", ["last_price", "closing_price", "price_change", "trade_volume", "trade_value"]],
    ["موقعیت", ["buy_open_positions", "sell_open_positions", "yesterday_open_positions"]],
    ["جریان پول", ["natural_money_flow", "legal_money_flow"]],
    ["حقیقی", ["natural_buy_count", "natural_buy_value", "natural_sell_count", "natural_sell_value"]],
    ["حقوقی", ["legal_buy_count", "legal_buy_value", "legal_sell_count", "legal_sell_value"]],
  ];

  let html = "";
  for (const [title, keys] of sections) {
    const rows = keys
      .filter((k) => row[k] != null)
      .map(
        (k) =>
          `<div class="detail-row"><span>${escapeHtml(DETAIL_LABELS[k] || k)}</span><span>${escapeHtml(formatDetailValue(k, row[k]))}</span></div>`
      );
    if (rows.length) {
      html += `<div class="detail-section-title">${escapeHtml(title)}</div><div class="detail-grid">${rows.join("")}</div>`;
    }
  }
  container.innerHTML = html || '<p class="detail-placeholder">جزئیات موجود نیست</p>';
}

function formatDetailValue(key, val) {
  if (Array.isArray(val)) return val.length ? val.join("، ") : "—";
  if (key === "option_type") return optionTypeLabel(val);
  if (key === "confidence") return fmtPct(val, 1);
  if (key.includes("share")) return fmtPct(val);
  if (key.includes("ratio")) return fmtRatio(val);
  if (key.includes("flow")) return fmtFlow(val);
  if (key.includes("value") || key.includes("volume") || key.includes("price") || key.includes("positions") || key.includes("interest")) {
    if (typeof val === "number") return fmtNum(val);
  }
  if (key.includes("date") || key === "end_date" || key === "rec_date") return fmtDate(val);
  return val ?? "—";
}

async function loadOiChart(insCode) {
  const block = document.getElementById("chartBlock");
  try {
    const data = await api(`/api/open-interest/${insCode}${dateQuery()}`);
    const history = data.history || [];
    if (!history.length) {
      block.classList.add("hidden");
      return;
    }
    block.classList.remove("hidden");
    const labels = history.map((h) => fmtDate(h.fetched_at));
    const buy = history.map((h) => h.buy_open_positions);
    const sell = history.map((h) => h.sell_open_positions);

    if (state.oiChart) state.oiChart.destroy();
    const ctx = document.getElementById("oiChart");
    state.oiChart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "موقعیت باز",
            data: buy,
            borderColor: "#38bdf8",
            backgroundColor: "rgba(56, 189, 248, 0.1)",
            tension: 0.3,
            fill: true,
          },
          {
            label: "فروش",
            data: sell,
            borderColor: "#a78bfa",
            backgroundColor: "rgba(167, 139, 250, 0.1)",
            tension: 0.3,
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: "#94a3b8", font: { family: "Vazirmatn" } } },
        },
        scales: {
          x: { ticks: { color: "#64748b", maxTicksLimit: 6 }, grid: { color: "rgba(148,163,184,0.1)" } },
          y: { ticks: { color: "#64748b" }, grid: { color: "rgba(148,163,184,0.1)" } },
        },
      },
    });
  } catch {
    block.classList.add("hidden");
  }
}

function populateExpiryFilter() {
  if (state.view !== "underlying") return;
  const select = document.getElementById("expiryFilter");
  const current = state.filters.expiry;
  const values = [...new Set(state.items.map((row) => row.end_date).filter(Boolean).map(String))].sort();
  select.innerHTML = '<option value="all">همه سررسیدها</option>' +
    values.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(fmtDate(value))}</option>`).join("");
  select.value = values.includes(current) ? current : "all";
  state.filters.expiry = select.value;
}

const ANALYSIS_SUM_FIELDS = [
  "natural_buy_count",
  "natural_buy_volume",
  "natural_buy_value",
  "natural_sell_count",
  "natural_sell_volume",
  "natural_sell_value",
  "legal_buy_count",
  "legal_buy_volume",
  "legal_buy_value",
  "legal_sell_count",
  "legal_sell_volume",
  "legal_sell_value",
  "buy_open_positions",
  "sell_open_positions",
  "yesterday_open_positions",
];

function emptyAnalysisBucket() {
  return ANALYSIS_SUM_FIELDS.reduce(
    (bucket, field) => {
      bucket[field] = 0;
      return bucket;
    },
    { contract_count: 0 }
  );
}

function emptyAnalysisModel() {
  return {
    call: { ITM: emptyAnalysisBucket(), OTM: emptyAnalysisBucket() },
    put: { ITM: emptyAnalysisBucket(), OTM: emptyAnalysisBucket() },
  };
}

function numericValue(value) {
  if (value == null || value === "") return 0;
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function buildAnalysisModel(rows) {
  const model = emptyAnalysisModel();
  rows.forEach((row) => {
    const optionType = row.option_type;
    const moneyness = row.moneyness;
    if (!model[optionType] || !model[optionType][moneyness]) return;
    const bucket = model[optionType][moneyness];
    bucket.contract_count += 1;
    ANALYSIS_SUM_FIELDS.forEach((field) => {
      bucket[field] += numericValue(row[field]);
    });
  });
  return model;
}

function sumRows(rows, getter) {
  return rows.reduce((total, row) => total + numericValue(getter(row)), 0);
}

function rowBuyVolume(row) {
  return numericValue(row.natural_buy_volume) + numericValue(row.legal_buy_volume);
}

function rowSellVolume(row) {
  return numericValue(row.natural_sell_volume) + numericValue(row.legal_sell_volume);
}

function rowParticipantBuyVolume(row, prefix) {
  return numericValue(row[`${prefix}_buy_volume`]);
}

function rowParticipantSellVolume(row, prefix) {
  return numericValue(row[`${prefix}_sell_volume`]);
}

function rowParticipantVolume(row, prefix) {
  return rowParticipantBuyVolume(row, prefix) + rowParticipantSellVolume(row, prefix);
}

function rowTradeVolume(row) {
  const tradeVolume = numericValue(row.trade_volume);
  return tradeVolume || Math.max(rowBuyVolume(row), rowSellVolume(row));
}

function ratioLabel(num, den) {
  if (!den) return num ? "∞" : "—";
  return (num / den).toLocaleString("fa-IR", { maximumFractionDigits: 2 });
}

function analysisMetricValue(value) {
  if (value == null) return "—";
  return typeof value === "number" ? fmtNum(value) : value;
}

function buildFourStepConclusion(rows, prefix, personLabel, personClass) {
  const callRows = rows.filter((row) => row.option_type === "call");
  const putRows = rows.filter((row) => row.option_type === "put");
  const itmRows = rows.filter((row) => row.moneyness === "ITM");
  const otmRows = rows.filter((row) => row.moneyness === "OTM");

  const callBuy = sumRows(callRows, (row) => rowParticipantBuyVolume(row, prefix));
  const callSell = sumRows(callRows, (row) => rowParticipantSellVolume(row, prefix));
  const putBuy = sumRows(putRows, (row) => rowParticipantBuyVolume(row, prefix));
  const putSell = sumRows(putRows, (row) => rowParticipantSellVolume(row, prefix));
  const itmVolume = sumRows(itmRows, (row) => rowParticipantVolume(row, prefix));
  const otmVolume = sumRows(otmRows, (row) => rowParticipantVolume(row, prefix));
  const callVolume = sumRows(callRows, (row) => rowParticipantVolume(row, prefix));
  const putVolume = sumRows(putRows, (row) => rowParticipantVolume(row, prefix));
  const hasCurrentOi = rows.some((row) => row.buy_open_positions != null);
  const hasYesterdayOi = rows.some((row) => row.yesterday_open_positions != null);
  const hasOi = hasCurrentOi || hasYesterdayOi;
  const currentOi = hasCurrentOi ? sumRows(rows, (row) => row.buy_open_positions) : null;
  const yesterdayOi = hasYesterdayOi ? sumRows(rows, (row) => row.yesterday_open_positions) : null;
  const oiChange = hasOi ? numericValue(currentOi) - numericValue(yesterdayOi) : null;

  const callBuyDominates = callBuy > callSell;
  const callSellDominates = callSell > callBuy;
  const putSellDominates = putSell > putBuy;
  const putBuyDominates = putBuy > putSell;
  const step1Score =
    (callBuyDominates ? 1 : callSellDominates ? -1 : 0) +
    (putSellDominates ? 1 : putBuyDominates ? -1 : 0);
  const step2Strong = otmVolume > itmVolume;
  const step2Cautious = itmVolume > otmVolume;
  const step3Bullish = callVolume > putVolume;
  const step4Confirm = oiChange != null && oiChange > 0;
  const step4Weak = oiChange != null && oiChange < 0;

  const score =
    step1Score +
    (step2Strong ? 2 : step2Cautious ? 1 : 0) +
    (step3Bullish ? 1 : callVolume < putVolume ? -1 : 0) +
    (step4Confirm ? 1 : step4Weak ? -1 : 0);

  let finalLabel = "خنثی";
  let finalClass = "neutral";
  if (score >= 5) {
    finalLabel = "صعودی قوی";
    finalClass = "bullish";
  } else if (score >= 3) {
    finalLabel = "صعودی محتاط";
    finalClass = "cautious";
  } else if (score <= -1) {
    finalLabel = "ضعیف";
    finalClass = "weak";
  }

  return {
    personLabel,
    personClass,
    finalLabel,
    finalClass,
    score,
    steps: [
      {
        kicker: "جریان سفارش",
        title: "حجم خرید و فروش",
        label: [
          callBuyDominates
            ? "Call: خرید بیشتر؛ صعودی"
            : callSellDominates
              ? "Call: فروش بیشتر؛ ضعیف"
              : "Call: متعادل",
          putSellDominates
            ? "Put: فروش بیشتر؛ صعودی"
            : putBuyDominates
              ? "Put: خرید بیشتر؛ ضعیف"
              : "Put: متعادل",
        ].filter(Boolean).join("، ") || "بدون برتری روشن",
        className: step1Score > 0 ? "bullish" : step1Score < 0 ? "weak" : "neutral",
        signals: [
          {
            label: callBuyDominates ? "Call صعودی" : callSellDominates ? "Call ضعیف" : "Call متعادل",
            className: callBuyDominates ? "bullish" : callSellDominates ? "weak" : "neutral",
          },
          {
            label: putSellDominates ? "Put صعودی" : putBuyDominates ? "Put ضعیف" : "Put متعادل",
            className: putSellDominates ? "bullish" : putBuyDominates ? "weak" : "neutral",
          },
        ],
        metrics: [
          ["Call خرید", callBuy],
          ["Call فروش", callSell],
          ["Put خرید", putBuy],
          ["Put فروش", putSell],
        ],
      },
      {
        kicker: "محدوده قیمت اعمال",
        title: "ITM و OTM",
        label: step2Strong ? "OTM غالب؛ مثبت‌تر" : step2Cautious ? "ITM غالب؛ مثبت محتاط" : "متعادل",
        className: step2Strong ? "bullish" : step2Cautious ? "cautious" : "neutral",
        metrics: [
          ["ITM", itmVolume],
          ["OTM", otmVolume],
        ],
      },
      {
        kicker: "ترکیب قراردادها",
        title: "نسبت Call به Put",
        label: step3Bullish ? "Call غالب" : callVolume < putVolume ? "Put غالب" : "متعادل",
        className: step3Bullish ? "bullish" : callVolume < putVolume ? "weak" : "neutral",
        metrics: [
          ["Call", callVolume],
          ["Put", putVolume],
          ["نسبت", ratioLabel(callVolume, putVolume)],
        ],
      },
      {
        kicker: "تأیید موقعیت",
        title: "Open Interest",
        label: !hasOi ? "داده موجود نیست" : step4Confirm ? "تأییدکننده" : step4Weak ? "تضعیف‌کننده" : "بدون تغییر",
        className: step4Confirm ? "bullish" : step4Weak ? "weak" : "neutral",
        metrics: [
          ["OI کل امروز", currentOi],
          ["OI کل دیروز", yesterdayOi],
          ["تغییر", oiChange],
        ],
      },
    ],
  };
}

function renderFourStepConclusion(rows) {
  const conclusions = [
    buildFourStepConclusion(rows, "natural", "حقیقی", "analysis-person-natural"),
    buildFourStepConclusion(rows, "legal", "حقوقی", "analysis-person-legal"),
  ];
  return `
    <section class="analysis-conclusion">
      <div class="analysis-conclusion-head">
        <span>نتیجه‌گیری چهارگام</span>
        <strong>تفکیک حقیقی / حقوقی</strong>
      </div>
      <div class="analysis-conclusion-groups">
        ${conclusions
          .map(
            (conclusion) => `
              <section class="analysis-conclusion-person analysis-conclusion-${conclusion.finalClass}">
                <div class="analysis-conclusion-person-head">
                  <span class="${conclusion.personClass}">${conclusion.personLabel}</span>
                  <strong>${conclusion.finalLabel}</strong>
                </div>
                <div class="analysis-step-grid">
	                  ${conclusion.steps
	                    .map(
	                      (step) => `
	                        <article class="analysis-step analysis-step-${step.className}">
	                          <div class="analysis-step-title">
	                            <span>${escapeHtml(step.kicker)}</span>
	                            <strong>${escapeHtml(step.title)}</strong>
	                          </div>
	                          ${step.signals
                              ? `<div class="analysis-step-labels">
                                  ${step.signals
                                    .map(
                                      (signal) => `
                                        <span class="analysis-step-label analysis-step-label-${signal.className}">
                                          ${escapeHtml(signal.label)}
                                        </span>`
                                    )
                                    .join("")}
                                </div>`
                              : `<div class="analysis-step-label">${escapeHtml(step.label)}</div>`}
	                          <div class="analysis-step-metrics">
	                            ${step.metrics
                                .map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(analysisMetricValue(value))}</strong></div>`)
                                .join("")}
	                          </div>
	                        </article>`
	                    )
	                    .join("")}
                </div>
              </section>`
          )
          .join("")}
      </div>
    </section>`;
}

function renderTrendShell() {
  return `
    <section class="analysis-conclusion trend-analysis" id="trendAnalysis">
      <div class="analysis-conclusion-head">
        <span>روند ۷ روزه تحلیل</span>
        <strong>در حال بارگذاری...</strong>
      </div>
      <div class="trend-loading">در حال آماده‌سازی روند تاریخی</div>
    </section>`;
}

async function loadTrendAnalysis() {
  const container = document.getElementById("trendAnalysis");
  if (!container || state.view !== "underlying" || !state.analysisVisible || !state.underlyingKey) return;
  const requestId = ++state.trendRequestId;
  try {
    const query = appendQuery({ days: "7" });
    const data = await api(`/api/underlyings/${encodeURIComponent(state.underlyingKey)}/trend${query}`);
    if (requestId !== state.trendRequestId) return;
    container.outerHTML = renderTrendAnalysis(data);
  } catch (e) {
    if (requestId !== state.trendRequestId) return;
    container.outerHTML = `
      <section class="analysis-conclusion trend-analysis">
        <div class="analysis-conclusion-head">
          <span>روند ۷ روزه تحلیل</span>
          <strong>خطا در دریافت داده</strong>
        </div>
        <div class="trend-loading">امکان ساخت روند تاریخی برای این تاریخ وجود ندارد</div>
      </section>`;
  }
}

function renderTrendAnalysis(data) {
  const items = data.items || [];
  if (!items.length) {
    return `
      <section class="analysis-conclusion trend-analysis">
        <div class="analysis-conclusion-head">
          <span>روند ۷ روزه تحلیل</span>
          <strong>داده کافی نیست</strong>
        </div>
        <div class="trend-loading">برای این سهم در بازه انتخابی داده تاریخی کافی پیدا نشد</div>
      </section>`;
  }
  return `
    <section class="analysis-conclusion trend-analysis">
      <div class="analysis-conclusion-head">
        <span>روند ۷ روزه تحلیل</span>
        <strong>${fmtNum(items.length)} روز معاملاتی</strong>
      </div>
      <div class="trend-summary-grid">
        ${renderTrendSummary("حقیقی", data.summary?.natural, "analysis-person-natural")}
        ${renderTrendSummary("حقوقی", data.summary?.legal, "analysis-person-legal")}
      </div>
      <div class="trend-tables">
        ${renderTrendPersonTable("حقیقی", "natural", items, "analysis-person-natural")}
        ${renderTrendPersonTable("حقوقی", "legal", items, "analysis-person-legal")}
      </div>
    </section>`;
}

function renderTrendSummary(label, summary, cls) {
  const className = summary?.class_name || "neutral";
  return `
    <article class="trend-summary-card trend-${className}">
      <span class="${cls}">${escapeHtml(label)}</span>
      <strong>${escapeHtml(summary?.label || "داده کافی نیست")}</strong>
      <small>میانگین اخیر: ${summary?.average_score == null ? "—" : fmtRatio(summary.average_score)}</small>
    </article>`;
}

function renderTrendPersonTable(label, key, items, cls) {
  return `
    <section class="trend-person">
      <div class="trend-person-title">
        <span class="${cls}">${escapeHtml(label)}</span>
        <strong>اعداد روزانه</strong>
      </div>
      <div class="trend-table-wrap">
        <table class="trend-table">
          <thead>
            <tr>
              <th>تاریخ</th>
              <th>نتیجه</th>
              <th>Call خ/ف</th>
              <th>Put خ/ف</th>
              <th>ITM/OTM</th>
              <th>Call/Put</th>
              <th>تغییر OI</th>
            </tr>
          </thead>
          <tbody>
            ${items.map((item) => renderTrendRow(item, key)).join("")}
          </tbody>
        </table>
      </div>
    </section>`;
}

function renderTrendRow(item, key) {
  const person = item.people?.[key] || {};
  const className = person.class_name || "neutral";
  const oi = person.has_open_interest ? fmtNum(person.open_interest_change) : "—";
  return `
    <tr>
      <td>${escapeHtml(fmtDate(item.date))}</td>
      <td><span class="trend-badge trend-${className}">${escapeHtml(person.label || "—")}</span></td>
      <td>${fmtNum(person.call_buy)} / ${fmtNum(person.call_sell)}</td>
      <td>${fmtNum(person.put_buy)} / ${fmtNum(person.put_sell)}</td>
      <td>${fmtNum(person.itm_volume)} / ${fmtNum(person.otm_volume)}</td>
      <td>${person.call_put_ratio == null ? "—" : fmtRatio(person.call_put_ratio)}</td>
      <td>${escapeHtml(oi)}</td>
    </tr>`;
}

function renderAnalysisSideSummary(typeModel) {
  const rows = [
    ["حقیقی", "natural", "analysis-person-natural"],
    ["حقوقی", "legal", "analysis-person-legal"],
  ];

  return `
    <section class="analysis-side-summary">
      <div class="analysis-side-summary-title">خلاصه</div>
      <div class="analysis-summary-list">
        ${rows
          .map(
            ([person, prefix, cls]) => `
              <article class="analysis-summary-row">
                <div class="analysis-summary-person ${cls}">${person}</div>
                <div class="analysis-summary-groups">
                  ${renderSummaryGroup("ITM", typeModel.ITM, prefix)}
                  ${renderSummaryGroup("OTM", typeModel.OTM, prefix)}
                  ${renderCombinedSummaryGroup(typeModel.ITM, typeModel.OTM, prefix)}
                </div>
              </article>`
          )
          .join("")}
      </div>
    </section>`;
}

function combinedMetric(a, b, prefix) {
  return {
    count: numericValue(a[`${prefix}_count`]) + numericValue(b[`${prefix}_count`]),
    volume: numericValue(a[`${prefix}_volume`]) + numericValue(b[`${prefix}_volume`]),
    value: numericValue(a[`${prefix}_value`]) + numericValue(b[`${prefix}_value`]),
  };
}

function renderCombinedSummaryMetric(a, b, prefix) {
  const metric = combinedMetric(a, b, prefix);
  return `
    <span class="analysis-metric analysis-metric-total">
      <strong>${fmtNum(metric.volume)}</strong>
    </span>`;
}

function renderSummaryGroup(label, bucket, prefix) {
  return `
    <div class="analysis-summary-group">
      <div class="analysis-summary-group-title">
        <span>${label}</span>
      </div>
      <div class="analysis-summary-pair">
        ${renderSummaryTile("خرید", bucket, `${prefix}_buy`)}
        ${renderSummaryTile("فروش", bucket, `${prefix}_sell`)}
        ${renderOpenInterestTile(bucket.buy_open_positions)}
      </div>
    </div>`;
}

function renderCombinedSummaryGroup(itm, otm, prefix) {
  const openInterest = numericValue(itm.buy_open_positions) + numericValue(otm.buy_open_positions);
  return `
    <div class="analysis-summary-group analysis-summary-group-total">
      <div class="analysis-summary-group-title">
        <span>جمع</span>
      </div>
      <div class="analysis-summary-pair">
        ${renderCombinedSummaryTile("خرید", itm, otm, `${prefix}_buy`)}
        ${renderCombinedSummaryTile("فروش", itm, otm, `${prefix}_sell`)}
        ${renderOpenInterestTile(openInterest)}
      </div>
    </div>`;
}

function renderSummaryTile(label, bucket, prefix) {
  return `
    <div class="analysis-summary-tile">
      <span>${label}</span>
      ${renderSummaryMetric(bucket, prefix)}
    </div>`;
}

function renderCombinedSummaryTile(label, itm, otm, prefix) {
  return `
    <div class="analysis-summary-tile">
      <span>${label}</span>
      ${renderCombinedSummaryMetric(itm, otm, prefix)}
    </div>`;
}

function renderOpenInterestTile(value) {
  return `
    <div class="analysis-summary-tile analysis-summary-oi-tile">
      <span>موقعیت</span>
      <strong>${fmtNum(value)}</strong>
    </div>`;
}

function renderSummaryMetric(bucket, prefix) {
  return `
    <span class="analysis-metric">
      <strong>${fmtNum(bucket[`${prefix}_volume`])}</strong>
    </span>`;
}

function renderAnalysisRows(bucket) {
  const rows = [
    ["حقیقی", "خرید", "natural_buy_count", "natural_buy_volume", "natural_buy_value", "analysis-person-natural"],
    ["حقیقی", "فروش", "natural_sell_count", "natural_sell_volume", "natural_sell_value", "analysis-person-natural"],
    ["حقوقی", "خرید", "legal_buy_count", "legal_buy_volume", "legal_buy_value", "analysis-person-legal"],
    ["حقوقی", "فروش", "legal_sell_count", "legal_sell_volume", "legal_sell_value", "analysis-person-legal"],
  ];

  return rows
    .map(
      ([person, side, countKey, volumeKey, valueKey, cls]) => `
        <tr>
          <td class="${cls}">${person}</td>
          <td>${side}</td>
          <td>${fmtNum(bucket[countKey])}</td>
          <td>${fmtNum(bucket[volumeKey])}</td>
          <td>${fmtNum(bucket[valueKey])}</td>
        </tr>`
    )
    .join("");
}

function renderAnalysisBucket(label, bucket) {
  return `
    <section class="analysis-bucket">
      <div class="analysis-bucket-header">
        <span>${label}</span>
        <span>${fmtNum(bucket.contract_count)} قرارداد</span>
      </div>
      <div class="analysis-oi-summary">
        <div>
          <span>موقعیت باز</span>
          <strong>${fmtNum(bucket.buy_open_positions)}</strong>
        </div>
        <div>
          <span>فروش باز</span>
          <strong>${fmtNum(bucket.sell_open_positions)}</strong>
        </div>
        <div>
          <span>موقعیت دیروز</span>
          <strong>${fmtNum(bucket.yesterday_open_positions)}</strong>
        </div>
      </div>
      <div class="analysis-table-wrap">
        <table class="analysis-table">
          <thead>
            <tr>
              <th>گروه</th>
              <th>سمت</th>
              <th>تعداد</th>
              <th>حجم</th>
              <th>ارزش</th>
            </tr>
          </thead>
          <tbody>${renderAnalysisRows(bucket)}</tbody>
        </table>
      </div>
    </section>`;
}

function renderAnalysisSide(type, title, model) {
  const total = model[type].ITM.contract_count + model[type].OTM.contract_count;
  return `
    <section class="analysis-side">
      <div class="analysis-side-title">
        <span>${title}</span>
        <span>${fmtNum(total)} قرارداد ITM/OTM</span>
      </div>
      ${renderAnalysisSideSummary(model[type])}
      <div class="analysis-buckets">
        ${renderAnalysisBucket("ITM", model[type].ITM)}
        ${renderAnalysisBucket("OTM", model[type].OTM)}
      </div>
    </section>`;
}

function renderAnalysis() {
  const panel = document.getElementById("analysisPanel");
  const content = document.getElementById("analysisContent");
  if (state.view !== "underlying" || !state.analysisVisible) {
    panel.classList.add("hidden");
    return;
  }

  const rows = state.filtered.filter((row) => row.moneyness === "ITM" || row.moneyness === "OTM");
  const model = buildAnalysisModel(rows);
  const underlyingName = state.underlying?.underlying_symbol || state.underlying?.underlying_short_name || "";
  document.getElementById("analysisTitle").textContent = underlyingName
    ? `آنالیز حقیقی / حقوقی ${underlyingName}${state.selectedDate ? ` - ${fmtDate(state.selectedDate)}` : ""}`
    : "آنالیز حقیقی / حقوقی";
  document.getElementById("analysisScope").textContent = `${fmtNum(rows.length)} قرارداد ITM/OTM`;
  content.innerHTML = renderFourStepConclusion(rows) + renderTrendShell() + renderAnalysisSide("call", "خرید", model) + renderAnalysisSide("put", "فروش", model);
  panel.classList.remove("hidden");
  loadTrendAnalysis();
}

function exportCsv() {
  if (!state.filtered.length) {
    showToast("داده برای خروجی موجود نیست", "error");
    return;
  }
  const config = VIEW_CONFIG[state.view];
  const keys = config.columns.map((c) => c.key);
  const header = config.columns.map((c) => c.label).join(",");
  const rows = state.filtered.map((row) =>
    keys.map((k) => {
      const v = row[k];
      const s = v == null ? "" : String(v);
      return s.includes(",") ? `"${s}"` : s;
    }).join(",")
  );
  const bom = "\uFEFF";
  const blob = new Blob([bom + header + "\n" + rows.join("\n")], { type: "text/csv;charset=utf-8;" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `tsetmc_${state.view}_${Date.now()}.csv`;
  a.click();
  showToast("فایل CSV دانلود شد");
}

let refreshPollTimer = null;

async function startRefresh() {
  const btn = document.getElementById("btnRefresh");
  btn.classList.add("loading");
  btn.disabled = true;
  try {
    const res = await api("/api/refresh", { method: "POST" });
    if (res.status === "already_running") {
      showToast("به‌روزرسانی در حال انجام است...", "success");
    } else {
      showToast("به‌روزرسانی شروع شد — ممکن است چند دقیقه طول بکشد");
    }
    pollRefreshStatus();
  } catch (e) {
    showToast("خطا در شروع به‌روزرسانی", "error");
    btn.classList.remove("loading");
    btn.disabled = false;
  }
}

function pollRefreshStatus() {
  clearInterval(refreshPollTimer);
  refreshPollTimer = setInterval(async () => {
    try {
      const st = await api("/api/refresh/status");
      if (st.message) setStatusText(st.message);
      if (st.running) {
        await loadSummary();
        if (st.message) setStatusText(st.message);
        await reloadActiveData();
        return;
      }
      clearInterval(refreshPollTimer);
      const btn = document.getElementById("btnRefresh");
      btn.classList.remove("loading");
      btn.disabled = false;
      if (st.last_error) {
        showToast(`خطا: ${st.last_error}`, "error");
        await loadSummary();
        await reloadActiveData();
      } else if (st.last_result) {
        showToast(`انجام شد — ${st.last_result.options} قرارداد`);
        await init();
      }
    } catch {
      clearInterval(refreshPollTimer);
    }
  }, 3000);
}

function bindSearch() {
  const input = document.getElementById("searchInput");
  let debounce;
  input.addEventListener("input", () => {
    clearTimeout(debounce);
    debounce = setTimeout(() => reloadActiveData(), 280);
  });
}

function bindFilters() {
  document.getElementById("dateFilter").addEventListener("change", async (event) => {
    state.selectedDate = event.target.value;
    state.selectedRowKey = null;
    state.selectedInsCode = null;
    state.underlying = null;
    syncDateToUrl();
    renderDetail(null);
    setStatusText("در حال دریافت داده تاریخ انتخابی...");
    setLoading(true);
    try {
      await loadSummary();
      await reloadActiveData();
      await loadDates();
      if (state.view === "underlying" && state.items.length) {
        selectRowByIndex(0);
      }
    } catch (e) {
      showToast("خطا در تغییر تاریخ", "error");
      console.error(e);
    } finally {
      setLoading(false);
    }
  });

  document.getElementById("btnAnalysis").addEventListener("click", () => {
    state.analysisVisible = !state.analysisVisible;
    updateViewChrome();
    renderAnalysis();
  });

  document.querySelectorAll("#typeFilter .segment").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#typeFilter .segment").forEach((el) => el.classList.remove("active"));
      btn.classList.add("active");
      state.filters.type = btn.dataset.type;
      state.selectedRowKey = null;
      state.selectedInsCode = null;
      renderDetail(null);
      applyFilterAndSort();
    });
  });

  document.getElementById("expiryFilter").addEventListener("change", (event) => {
    state.filters.expiry = event.target.value;
    applyFilterAndSort();
  });
  document.getElementById("moneynessFilter").addEventListener("change", (event) => {
    state.filters.moneyness = event.target.value;
    applyFilterAndSort();
  });
  document.getElementById("strikeMinFilter").addEventListener("input", (event) => {
    state.filters.strikeMin = event.target.value;
    applyFilterAndSort();
  });
  document.getElementById("strikeMaxFilter").addEventListener("input", (event) => {
    state.filters.strikeMax = event.target.value;
    applyFilterAndSort();
  });
}

async function init() {
  setLoading(true);
  try {
    updateViewChrome();
    await loadDates();
    await loadSummary();
    await reloadActiveData();
    if (state.view === "underlying" && state.items.length && !state.selectedRowKey) {
      selectRowByIndex(0);
    }
  } catch (e) {
    showToast("خطا در بارگذاری داده", "error");
    console.error(e);
  } finally {
    setLoading(false);
  }
}

document.getElementById("btnRefresh").addEventListener("click", startRefresh);
document.getElementById("btnExport").addEventListener("click", exportCsv);
document.getElementById("btnBack").addEventListener("click", () => {
  window.location.href = `/${dateQuery()}`;
});
document.getElementById("closeDetail").addEventListener("click", () => {
  state.selectedInsCode = null;
  state.selectedRowKey = null;
  renderTable();
  renderDetail(null);
});

bindSearch();
bindFilters();
init();
