// Control page: builds the controls from /api/meta, keeps them in step with settings.txt
// (/api/state), and saves every change. All text comes from the API and is set with
// textContent, never as HTML.

const $ = (selector) => document.querySelector(selector);
const SAVE_DELAY_MS = 80;       // wait for a slider drag to settle before writing
const POLL_MS = 1000;           // pick up hand edits to settings.txt
const QUIET_MS = 1500;          // do not overwrite the page right after you touched it

let meta;
let state;
let saveTimer = null;
let lastTouch = 0;

const rows = new Map();         // shape field name -> { row, range, number }
const expressionButtons = new Map();
const voiceButtons = new Map();
const colorButtons = new Map();

// ---- talking to the server ------------------------------------------------------------------

async function request(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error([].concat(body.detail ?? response.statusText).join(", "));
  }
  return response;
}

function setStatus(text, kind = "") {
  const status = $("#status");
  status.textContent = text;
  status.className = `status ${kind}`;
}

function scheduleSave() {
  lastTouch = Date.now();
  setStatus("Saving");
  clearTimeout(saveTimer);
  saveTimer = setTimeout(save, SAVE_DELAY_MS);
}

async function save() {
  saveTimer = null;
  try {
    await request("/api/state", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state),
    });
    setStatus("Saved", "ok");
  } catch (error) {
    setStatus(error.message, "bad");
  }
}

async function poll() {
  if (saveTimer || Date.now() - lastTouch < QUIET_MS) return;
  try {
    const latest = await (await request("/api/state")).json();
    if (JSON.stringify(latest) !== JSON.stringify(state)) {
      state = latest;
      sync();
    }
    setStatus("Connected", "ok");
  } catch (error) {
    setStatus("Control server not reachable", "bad");
  }
}

// ---- building the controls ------------------------------------------------------------------

function chip(label, onClick) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.addEventListener("click", onClick);
  return button;
}

function buildChips(container, names, buttons, onPick) {
  for (const name of names) {
    const button = chip(name, () => onPick(name));
    buttons.set(name, button);
    container.append(button);
  }
}

function buildColors() {
  for (const { name, rgb } of meta.colors) {
    const button = chip("", () => {
      state.color = name;
      scheduleSave();
      sync();
    });
    button.style.background = `rgb(${rgb.join(",")})`;
    button.title = name;
    button.setAttribute("aria-label", name);
    colorButtons.set(name, button);
    $("#colors").append(button);
  }
}

function buildShape() {
  const groups = new Map();
  for (const field of meta.fields) {
    if (!groups.has(field.group)) {
      const set = document.createElement("fieldset");
      const legend = document.createElement("legend");
      legend.textContent = field.group;
      set.append(legend);
      groups.set(field.group, set);
      $("#shape").append(set);
    }
    groups.get(field.group).append(buildRow(field));
  }
}

function buildRow(field) {
  const row = document.createElement("div");
  row.className = "row";

  const label = document.createElement("label");
  label.textContent = field.name;
  label.htmlFor = `shape-${field.name}`;

  const range = Object.assign(document.createElement("input"), {
    type: "range", id: `shape-${field.name}`, min: field.min, max: field.max, step: 1,
  });
  const number = Object.assign(document.createElement("input"), {
    type: "number", min: field.min, max: field.max, step: 1,
  });
  number.setAttribute("aria-label", `${field.name} value`);
  const undo = chip("↶", () => setShapeValue(field.name, null));
  undo.className = "undo";
  undo.title = "Back to the expression's value";
  undo.setAttribute("aria-label", `Reset ${field.name}`);

  const onInput = (event) => {
    if (event.target.value === "") return;
    setShapeValue(field.name, Number(event.target.value));
  };
  range.addEventListener("input", onInput);
  number.addEventListener("input", onInput);

  row.append(label, range, number, undo);
  rows.set(field.name, { row, range, number });
  return row;
}

// ---- state changes --------------------------------------------------------------------------

function expressionValues() {
  return meta.expressions.find((e) => e.name === state.expression).values;
}

// value === null puts the field back to the expression's own value.
function setShapeValue(name, value) {
  if (value === null || value === expressionValues()[name]) delete state.shape[name];
  else state.shape[name] = value;
  scheduleSave();
  sync();
}

function pickExpression(name) {
  state.expression = name;
  state.shape = {};   // tweaks belong to one expression
  scheduleSave();
  sync();
}

function bindSimpleControls() {
  buildChips($("#expressions"), meta.expressions.map((e) => e.name), expressionButtons, pickExpression);
  buildChips($("#voices"), meta.voices, voiceButtons, (name) => {
    state.voice = name;
    scheduleSave();
    sync();
  });
  buildColors();

  for (const id of ["speaking", "idle_motion"]) {
    $(`#${id}`).addEventListener("change", (event) => {
      state[id] = event.target.checked;
      scheduleSave();
    });
  }
  const fps = $("#fps");
  Object.assign(fps, { min: meta.fps.min, max: meta.fps.max, step: meta.fps.step });
  fps.addEventListener("input", () => {
    state.fps = Number(fps.value);
    scheduleSave();
    sync();
  });

  $("#reset-shape").addEventListener("click", () => {
    state.shape = {};
    scheduleSave();
    sync();
  });
  $("#copy-cpp").addEventListener("click", copyCpp);
}

async function copyCpp() {
  clearTimeout(saveTimer);
  await save();   // export reads settings.txt, so write the latest first
  const code = await (await request("/api/export")).text();
  const pre = $("#cpp");
  pre.textContent = code;
  pre.hidden = false;
  try {
    await navigator.clipboard.writeText(code);
    setStatus("Copied to the clipboard", "ok");
  } catch {
    setStatus("Copy it from the box below", "");
  }
}

// ---- showing the state ----------------------------------------------------------------------

function sync() {
  for (const [name, button] of expressionButtons) button.setAttribute("aria-pressed", name === state.expression);
  for (const [name, button] of voiceButtons) button.setAttribute("aria-pressed", name === state.voice);
  for (const [name, button] of colorButtons) button.setAttribute("aria-pressed", name === state.color);
  $("#speaking").checked = state.speaking;
  $("#idle_motion").checked = state.idle_motion;
  $("#fps").value = state.fps;
  $("#fps-value").textContent = `${state.fps} fps`;

  const base = expressionValues();
  for (const [name, { row, range, number }] of rows) {
    const changed = name in state.shape;
    const value = changed ? state.shape[name] : base[name];
    row.classList.toggle("changed", changed);
    if (document.activeElement !== range) range.value = value;
    if (document.activeElement !== number) number.value = value;
  }
}

async function init() {
  try {
    meta = await (await request("/api/meta")).json();
    state = await (await request("/api/state")).json();
  } catch (error) {
    setStatus(`Cannot load: ${error.message}`, "bad");
    return;
  }
  bindSimpleControls();
  buildShape();
  sync();
  setStatus("Connected", "ok");
  setInterval(poll, POLL_MS);
}

init();
