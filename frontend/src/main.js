// Copyright (C) New Community Church SE London 2026.
// For licensing information see ../../LICENSE.md

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
  row.querySelector('input:not([type="hidden"])').focus(); // ✨ past the row's contact id
}

// ✨ A saved list sends back each row's contact id as it now is; put them back into the rows, so the next save
// edits the people this one kept rather than adding them again (which would stop their observers' links).
// A refusal about one row of a list names the field at fault; mark it (red, and aria-invalid for a screen
// reader) until a save goes through. Rows are counted from 1, as the refusal words them.
document.addEventListener("htmx:afterSwap", (event) => {
  const status = event.detail.target;
  const rows = status.classList?.contains("save-status") && status.closest("form")?.querySelector(".contact-rows");
  if (!rows) return;
  const saved = status.querySelector("[data-contact-ids]");
  saved?.dataset.contactIds.split(",").forEach((id, row) => {
    const field = rows.children[row]?.querySelector('input[name="contact"]');
    if (field) field.value = id;
  });
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

// ✨ Each coach checklist screen takes the last one's place in the page, which leaves the window where it was: after
// "Continue →" from the short intro, part way down the long questions. As a new page would, bring a screen whose top
// has gone out of view back to it, and move the focus to its heading, so a screen reader says where they now are
// (ticket 41e). Only for a new screen: the same one sent back (a refusal beside its button, a coach's link issued or
// revoked) stays where it is. htmx fires this on the new screen itself.
let checklistScreenBefore = null;

document.addEventListener("htmx:beforeRequest", (event) => {
  const checklist = event.target.closest?.(".coach-checklist");
  if (checklist) checklistScreenBefore = checklist.dataset.screen;
});

document.addEventListener("htmx:afterSettle", (event) => {
  const checklist = event.target;
  if (!checklist.classList?.contains("coach-checklist")) return;
  if (checklist.dataset.screen === checklistScreenBefore) return;
  if (checklist.getBoundingClientRect().top < 0) checklist.scrollIntoView({ block: "start" });
  const heading = checklist.querySelector("h2");
  if (!heading || checklist.contains(document.activeElement)) return;
  heading.tabIndex = -1;
  heading.focus({ preventScroll: true });
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

// ✨ The homepage's menu is a <details>, so it opens without JavaScript; with it, following a link closes the menu.
document.addEventListener("click", (event) => {
  const menu = event.target.closest("[data-closes-on-link]");
  if (!menu || !event.target.closest("a")) return;
  menu.open = false;
});

// ✨ The homepage's forest moves only for those who have not asked their device for less motion. It is started here
// rather than by `autoplay`, which would play before this check could stop it; everyone else, and anyone without
// JavaScript, sees the still frame.
if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
  document.querySelectorAll("video[data-plays-unless-reduced-motion]").forEach((video) => {
    video.play().catch(() => {}); // ✨ a browser that refuses keeps the still frame
  });
}

mountSorts();
