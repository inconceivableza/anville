import "./styles.css";
import htmx from "htmx.org";

// ✨ Defence in depth: htmx may not run code from hx-* attributes. See ADR 0006 before changing.
htmx.config.allowEval = false;

// ✨ A refused answer (400) carries the reason, so show it where "Saved" would go. htmx's default
// leaves every 4xx and 5xx unswapped.
htmx.config.responseHandling = [{ code: "400", swap: true, error: true }, ...htmx.config.responseHandling];

window.htmx = htmx;
document.documentElement.dataset.javascript = "loaded";

// ✨ Keep the autosave status honest: never leave an earlier "Saved" showing while a save is in flight
// or after one has failed without a reason from the server.
function saveStatus(event) {
  const target = event.detail.target ?? event.detail.requestConfig?.target;
  return target?.classList.contains("save-status") ? target : null;
}

document.addEventListener("htmx:beforeRequest", (event) => {
  const status = saveStatus(event);
  if (status) status.textContent = "Saving…";
});

function notSaved(event) {
  const status = saveStatus(event);
  if (status && event.detail.xhr?.status !== 400) {
    status.textContent = "Not saved. Check your connection, then try again.";
  }
}

document.addEventListener("htmx:responseError", notSaved);
document.addEventListener("htmx:sendError", notSaved);
