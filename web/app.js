const SUMMARY_URL = "../results/summary_results.json";
const ERROR_URL = "../results/run_errors.json";
const TASKS_URL = "../tasks/";
const TRANSCRIPTS_URL = "../transcripts/";
const WEIGHTS = {
  ledger_balances: 0.5,
  reconciling_items: 0.25,
  ignored_event_ids: 0.15,
  final_status: 0.1,
};
const DIMENSION_LABELS = {
  ledger_balances: "Ledger balances",
  reconciling_items: "Reconciliation items",
  ignored_event_ids: "Ignored event IDs",
  final_status: "Final status",
};

const state = { summary: null, errors: [], tasks: new Map(), transcripts: new Map() };
const el = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};

function slug(value) {
  return value.replace(/[^A-Za-z0-9._-]+/g, "_").replace(/^[._-]+|[._-]+$/g, "") || "model";
}

function pct(value, digits = 1) {
  return `${(Number(value || 0) * 100).toFixed(digits)}%`;
}

function scoreText(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

function shortModel(modelId) {
  const name = modelId.split("/").at(-1) || modelId;
  return name.replace(":free", "");
}

function taskLabel(taskId) {
  return taskId.replace(/^task_\d+_/, "").replaceAll("_", " ");
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText} while loading ${url}`);
  return response.json();
}

async function loadTranscript(modelId, taskId) {
  const key = `${modelId}::${taskId}`;
  if (state.transcripts.has(key)) return state.transcripts.get(key);
  const path = `${TRANSCRIPTS_URL}${slug(modelId)}/${taskId}_trial_1.json`;
  const record = await fetchJson(path);
  state.transcripts.set(key, record);
  return record;
}

async function loadTaskDescription(taskId) {
  if (state.tasks.has(taskId)) return state.tasks.get(taskId);
  const task = await fetchJson(`${TASKS_URL}${taskId}.json`);
  const description = task.metadata?.scenario || task.metadata?.title || task.description || task.title || "Synthetic ledger reconciliation case.";
  state.tasks.set(taskId, description);
  return description;
}

function renderOverview() {
  const models = state.summary.models;
  const scored = models.reduce((total, model) => total + model.trial_count, 0);
  const expected = models.reduce((total, model) => total + model.expected_trial_count, 0);
  const strictPasses = models.reduce((total, model) => total + Math.round(model.strict_pass_rate * model.trial_count), 0);
  const weightedMean = models.reduce((total, model) => total + model.mean_partial_score * model.trial_count, 0) / Math.max(scored, 1);
  const cards = [
    ["Responses scored", `${scored} / ${expected}`, "All requested model-task pairs"],
    ["Strict passes", `${strictPasses} / ${scored}`, "Exact schema and accounting match"],
    ["Models", `${models.length}`, "Explicit OpenRouter :free routes"],
    ["Mean partial score", pct(weightedMean), "Across scored responses"],
  ];
  const grid = document.querySelector("#overview");
  grid.replaceChildren(...cards.map(([label, value, foot]) => {
    const card = el("article", "metric-card");
    card.append(el("div", "metric-label", label), el("div", "metric-value", value), el("div", "metric-foot", foot));
    return card;
  }));
}

function renderLeaderboard() {
  const rows = [...state.summary.models].sort((a, b) => b.mean_partial_score - a.mean_partial_score);
  const body = document.querySelector("#leaderboard-body");
  body.replaceChildren(...rows.map((model, index) => {
    const row = document.createElement("tr");
    const nameCell = document.createElement("td");
    const name = el("span", "model-name", shortModel(model.model_id));
    name.title = model.model_id;
    nameCell.append(name, el("span", "model-provider", index === 0 ? "HIGHEST PARTIAL MEAN" : model.model_id.split("/")[0]));

    const coverage = document.createElement("td");
    coverage.textContent = `${model.trial_count} / ${model.expected_trial_count}`;
    coverage.className = "mono";

    const scoreCell = document.createElement("td");
    scoreCell.className = "score-cell";
    const line = el("div", "score-line");
    line.append(el("span", "", scoreText(model.mean_partial_score)), el("span", "muted", "partial"));
    const track = el("div", "score-track");
    const fill = document.createElement("span");
    fill.style.width = `${Math.max(0, Math.min(100, model.mean_partial_score * 100))}%`;
    track.append(fill);
    scoreCell.append(line, track);

    const strictCell = document.createElement("td");
    const strictBadge = el("span", model.strict_pass_rate > 0 ? "badge badge-pass" : "badge badge-fail", `${Math.round(model.strict_pass_rate * model.trial_count)} pass`);
    strictCell.append(strictBadge);

    const latency = el("td", "mono", `${model.mean_latency_seconds.toFixed(2)} s`);
    const cost = el("td", "mono", model.total_run_cost_usd === null ? "N/A" : `$${model.total_run_cost_usd.toFixed(2)}`);
    row.append(nameCell, coverage, scoreCell, strictCell, latency, cost);
    return row;
  }));
}

function populateSelectors() {
  const modelSelect = document.querySelector("#model-select");
  const taskSelect = document.querySelector("#task-select");
  for (const model of state.summary.models) {
    const option = document.createElement("option");
    option.value = model.model_id;
    option.textContent = shortModel(model.model_id);
    modelSelect.append(option);
  }
  for (const taskId of state.summary.task_ids) {
    const option = document.createElement("option");
    option.value = taskId;
    option.textContent = `${taskId.replace(/^task_\d+_/, "Task ")}`;
    taskSelect.append(option);
  }
  modelSelect.value = state.summary.models.slice().sort((a, b) => b.mean_partial_score - a.mean_partial_score)[0].model_id;
  modelSelect.addEventListener("change", renderSelectedTranscript);
  taskSelect.addEventListener("change", renderTask);
}

function renderTagList(tags) {
  if (!tags?.length) return el("span", "empty-cell", "No automated mismatch tags");
  const list = el("div", "tag-list");
  for (const tag of tags) list.append(el("span", "tag-pill", tag));
  return list;
}

function renderTaskRows(records) {
  const body = document.querySelector("#task-results-body");
  body.replaceChildren(...records.map(({ modelId, record }) => {
    const row = document.createElement("tr");
    const modelCell = document.createElement("td");
    const selectButton = el("button", "select-model", shortModel(modelId));
    selectButton.type = "button";
    selectButton.title = `Inspect ${modelId}`;
    selectButton.addEventListener("click", () => {
      document.querySelector("#model-select").value = modelId;
      renderSelectedTranscript();
    });
    modelCell.append(selectButton);
    const scoreCell = el("td", "mono", scoreText(record.grader.total_score));
    const strictCell = document.createElement("td");
    strictCell.append(el("span", record.grader.passed ? "badge badge-pass" : "badge badge-fail", record.grader.passed ? "PASS" : "FAIL"));
    const tagsCell = document.createElement("td");
    tagsCell.className = "tags";
    tagsCell.textContent = record.automated_failure_tags?.join(" · ") || "—";
    row.append(modelCell, scoreCell, strictCell, tagsCell);
    row.addEventListener("click", (event) => {
      if (event.target !== selectButton) {
        document.querySelector("#model-select").value = modelId;
        renderSelectedTranscript();
      }
    });
    row.tabIndex = 0;
    row.setAttribute("aria-label", `${shortModel(modelId)}, score ${scoreText(record.grader.total_score)}, ${record.grader.passed ? "strict pass" : "strict fail"}`);
    return row;
  }));
}

function renderDimensionBars(scores = {}) {
  const container = el("div", "dimensions");
  for (const [key, weight] of Object.entries(WEIGHTS)) {
    const contribution = Number(scores[key] || 0);
    const share = Math.max(0, Math.min(100, contribution / weight * 100));
    const row = el("div", "dimension-row");
    row.append(el("span", "dimension-label", DIMENSION_LABELS[key]));
    const track = el("div", "score-track");
    const fill = document.createElement("span");
    fill.style.width = `${share}%`;
    track.append(fill);
    row.append(track, el("span", "dimension-value", `${share.toFixed(0)}%`));
    container.append(row);
  }
  return container;
}

function renderTranscript(record) {
  const panel = document.querySelector("#response-detail");
  const grader = record.grader;
  const header = el("div", "detail-title");
  header.append(el("span", "detail-score", scoreText(grader.total_score)), el("span", grader.passed ? "badge badge-pass" : "badge badge-fail", grader.passed ? "STRICT PASS" : "STRICT FAIL"));

  const metadata = el("div", "detail-meta");
  const usage = record.token_usage || {};
  const values = [
    ["LATENCY", `${(record.latency_ms / 1000).toFixed(2)} s`],
    ["TOKENS", `${usage.total_tokens ?? "—"}`],
    ["REPORTED COST", record.estimated_usd_cost === null ? "N/A" : `$${Number(record.estimated_usd_cost).toFixed(4)}`],
  ];
  for (const [label, value] of values) {
    const item = document.createElement("div");
    item.append(el("span", "", label), el("strong", "", value));
    metadata.append(item);
  }

  const frag = document.createDocumentFragment();
  frag.append(header, metadata, el("h3", "subheading", "Weighted dimension scores"), renderDimensionBars(grader.dimension_scores));
  frag.append(el("h3", "subheading", "Observed mismatch tags"), renderTagList(grader.failure_tags || []));

  const outputDetails = document.createElement("details");
  outputDetails.append(el("summary", "", "Model response"));
  outputDetails.append(el("pre", "", record.raw_model_response || "No response text was saved."));
  const promptDetails = document.createElement("details");
  promptDetails.append(el("summary", "", "Full task prompt"));
  promptDetails.append(el("pre", "", record.prompt || "No prompt was saved."));
  const discrepancyDetails = document.createElement("details");
  discrepancyDetails.append(el("summary", "", "Grader discrepancy details"));
  discrepancyDetails.append(el("pre", "", JSON.stringify(grader.discrepancies || {}, null, 2)));
  frag.append(outputDetails, promptDetails, discrepancyDetails);
  panel.replaceChildren(frag);
}

async function renderSelectedTranscript() {
  const modelId = document.querySelector("#model-select").value;
  const taskId = document.querySelector("#task-select").value;
  const panel = document.querySelector("#response-detail");
  panel.replaceChildren(el("p", "muted", "Loading saved response…"));
  try {
    renderTranscript(await loadTranscript(modelId, taskId));
  } catch (error) {
    panel.replaceChildren(el("p", "muted", `Could not load this transcript: ${error.message}`));
  }
}

async function renderTask() {
  const taskId = document.querySelector("#task-select").value;
  const taskDescription = document.querySelector("#task-description");
  const body = document.querySelector("#task-results-body");
  body.replaceChildren();
  taskDescription.textContent = "Loading task details…";
  try {
    const [description, ...records] = await Promise.all([
      loadTaskDescription(taskId),
      ...state.summary.models.map(async (model) => ({ modelId: model.model_id, record: await loadTranscript(model.model_id, taskId) })),
    ]);
    taskDescription.textContent = description;
    renderTaskRows(records);
    await renderSelectedTranscript();
  } catch (error) {
    taskDescription.textContent = `Could not load this task: ${error.message}`;
  }
}

async function start() {
  const status = document.querySelector("#load-status");
  try {
    const [summary, errors] = await Promise.all([fetchJson(SUMMARY_URL), fetchJson(ERROR_URL)]);
    state.summary = summary;
    state.errors = errors;
    renderOverview();
    renderLeaderboard();
    populateSelectors();
    status.textContent = errors.length ? `${errors.length} provider request(s) are unscored; see the detailed report.` : "All saved responses loaded. Selecting a task does not make live model calls.";
    await renderTask();
  } catch (error) {
    status.className = "load-status error";
    status.textContent = `Could not load the evaluation data (${error.message}). Start the local server from the repository root: python -m http.server 8000, then open http://localhost:8000/web/.`;
  }
}

start();
