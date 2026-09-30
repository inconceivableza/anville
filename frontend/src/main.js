import "./styles.css";
import htmx from "htmx.org";
import { mountSorts } from "./sort.js";

// ✨ Defence in depth: htmx may not run code from hx-* attributes. See ADR 0006 before changing.
htmx.config.allowEval = false;

// ✨ A refused answer (400) or a second sort (409) carries the reason, so show it where "Saved" would go.
// htmx's default leaves every 4xx and 5xx unswapped.
const REFUSED_WITH_A_REASON = [400, 409];
htmx.config.responseHandling = [
  { code: `^(${REFUSED_WITH_A_REASON.join("|")})$`, swap: true, error: true },
  ...htmx.config.responseHandling,
];

window.htmx = htmx;
document.documentElement.dataset.javascript = "loaded";

// ✨ Keep the autosave status honest without flicker. "Saved" disappears as soon as the participant changes
// their answer, because it no longer describes what is on screen. A quick save then shows "Saved" again
// directly; "Saving…" appears only when a save is slow; a failure without a reason from the server says so.
const SLOW_SAVE_MS = 600;
const slowSaveTimers = new WeakMap();

function saveStatus(event) {
  const target = event.detail.target ?? event.detail.requestConfig?.target;
  return target?.classList.contains("save-status") ? target : null;
}

document.addEventListener("input", (event) => {
  const status = event.target.closest("form")?.querySelector(".save-status");
  if (status) status.textContent = "";
});

document.addEventListener("htmx:beforeRequest", (event) => {
  const status = saveStatus(event);
  if (!status) return;
  clearTimeout(slowSaveTimers.get(status));
  slowSaveTimers.set(status, setTimeout(() => (status.textContent = "Saving…"), SLOW_SAVE_MS));
});

document.addEventListener("htmx:afterRequest", (event) => {
  const status = saveStatus(event);
  if (status) clearTimeout(slowSaveTimers.get(status));
});

function notSaved(event) {
  const status = saveStatus(event);
  if (status && !REFUSED_WITH_A_REASON.includes(event.detail.xhr?.status)) {
    status.textContent = "Not saved. Check your connection, then try again.";
  }
}

document.addEventListener("htmx:responseError", notSaved);
document.addEventListener("htmx:sendError", notSaved);

// ✨ Near a text box's length limit, say how much room is left; the browser stops typing at the limit itself.
const SHOW_LENGTH_LEFT_BELOW = 0.1;

function showLengthLeft(textarea) {
  const hint = document.getElementById(textarea.getAttribute("aria-describedby"));
  if (!hint) return;
  const max = textarea.maxLength;
  const left = max - textarea.value.length;
  hint.hidden = left > max * SHOW_LENGTH_LEFT_BELOW;
  hint.textContent =
    left > 0
      ? `${left.toLocaleString("en-GB")} characters left.`
      : `You have reached the ${max.toLocaleString("en-GB")}-character limit.`;
}

document.addEventListener("input", (event) => {
  if (event.target.matches("textarea[maxlength]")) showLengthLeft(event.target);
});
document.querySelectorAll("textarea[maxlength]").forEach(showLengthLeft);

// ✨ A contact list's "add another": with JavaScript a row is added in the page, rather than the button saving the
// list and reloading. The new row copies the last one, emptied and numbered, and takes the focus. Nothing is
// saved until something is typed into it, and an empty row is never kept.
const MAX_CONTACT_ROWS = 50; // ✨ the server's MAX_CONTACTS

function addContactRow(button) {
  const rows = button.closest("form").querySelector(".contact-rows");
  const row = rows.lastElementChild.cloneNode(true);
  const number = rows.children.length + 1;
  row.querySelector(".contact-num").textContent = number;
  row.querySelectorAll(".visually-hidden").forEach((label) => {
    label.textContent = label.textContent.replace(/^Person \d+/, `Person ${number}`);
  });
  row.querySelectorAll("input").forEach((input) => (input.value = ""));
  rows.append(row);
  button.value = number + 1;
  button.disabled = number >= MAX_CONTACT_ROWS;
  row.querySelector("input").focus();
}

// ✨ A refusal about one row of a list names the field at fault; mark it (red, and aria-invalid for a screen
// reader) until a save goes through. Rows are counted from 1, as the refusal words them.
document.addEventListener("htmx:afterSwap", (event) => {
  const status = event.detail.target;
  const rows = status.classList?.contains("save-status") && status.closest("form")?.querySelector(".contact-rows");
  if (!rows) return;
  rows.querySelectorAll("[aria-invalid]").forEach((input) => input.removeAttribute("aria-invalid"));
  const marked = status.querySelector("[data-invalid-row]");
  if (!marked) return;
  const row = rows.children[Number(marked.dataset.invalidRow) - 1];
  row?.querySelector(`input[name="${marked.dataset.invalidField}"]`)?.setAttribute("aria-invalid", "true");
});

document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-add-row]");
  if (!button) return;
  event.preventDefault();
  addContactRow(button);
});

// ✨ Copy an issued observer link, as the prototype's Copy button does. Without JavaScript the field is still there
// to select and copy by hand.
document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-copy]");
  if (!button) return;
  const field = document.getElementById(button.dataset.copy);
  field.select();
  try {
    await navigator.clipboard.writeText(field.value);
    button.textContent = "Copied";
  } catch {
    button.textContent = "Select and copy it";
  }
});

mountSorts();
