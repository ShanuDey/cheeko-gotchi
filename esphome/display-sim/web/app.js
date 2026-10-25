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

async function restartSimulator() {
  setStatus("Restarting the simulator");
  try {
    await request("/api/restart", { method: "POST" });
    setStatus("Simulator restarting, the window reopens in a few seconds", "ok");
  } catch (error) {
    setStatus(error.message, "bad");
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

function bindControls() {
  buildChips($("#expressions"), meta.expressions, expressionButtons, (name) => {
    state.expression = name;
    scheduleSave();
    sync();
  });
  buildChips($("#voices"), meta.voices, voiceButtons, (name) => {
    state.voice = name;
    scheduleSave();
    sync();
  });
  buildColors();

  $("#speaking").addEventListener("change", (event) => {
    state.speaking = event.target.checked;
    scheduleSave();
  });
  const fps = $("#fps");
  Object.assign(fps, { min: meta.fps.min, max: meta.fps.max, step: meta.fps.step });
  fps.addEventListener("input", () => {
    state.fps = Number(fps.value);
    scheduleSave();
    sync();
  });
  $("#restart").addEventListener("click", restartSimulator);
}

// ---- showing the state ----------------------------------------------------------------------

function sync() {
  for (const [name, button] of expressionButtons) button.setAttribute("aria-pressed", name === state.expression);
  for (const [name, button] of voiceButtons) button.setAttribute("aria-pressed", name === state.voice);
  for (const [name, button] of colorButtons) button.setAttribute("aria-pressed", name === state.color);
  $("#speaking").checked = state.speaking;
  $("#fps").value = state.fps;
  $("#fps-value").textContent = `${state.fps} fps`;
}

async function init() {
  try {
    meta = await (await request("/api/meta")).json();
    state = await (await request("/api/state")).json();
  } catch (error) {
    setStatus(`Cannot load: ${error.message}`, "bad");
    return;
  }
  bindControls();
  sync();
  setStatus("Connected", "ok");
  setInterval(poll, POLL_MS);
}

init();
