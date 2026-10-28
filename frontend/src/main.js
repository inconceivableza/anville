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

// ✨ A contact list's empty row is no form of its own (fix-1), so its status is found by the row's fields' wrapper.
document.addEventListener("input", (event) => {
  const status = event.target.closest("form, .contact-person")?.querySelector(".save-status");
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

// ✨ An autosaved answer is saved as it changes, so its form is never submitted as a page while JavaScript runs:
// Enter in it would otherwise send it through the hidden fallback button and reload the page (fix-7). Without
// JavaScript, that button and Enter still save it.
// ✨ A contact list's Save belongs to the list's one form, not its row's (fix-1), hence the submitter too.
document.addEventListener("submit", (event) => {
  const fallback = event.target.querySelector(".save-fallback") || event.submitter?.matches(".save-fallback");
  if (fallback) event.preventDefault();
});

// ✨ A contact list's rows all belong to its one form (fix-1), whose Enter presses the first row's button, wherever it
// was typed. Do as when each row was a form of its own instead: an empty row's Enter presses its own "Get link", and a
// person's saves their row now, as its autosave does. Without JavaScript, Enter presses the first row's button, which
// saves every edit and brings every row's typing back.
document.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || event.isComposing || !event.target.matches?.("input")) return;
  const row = event.target.closest(".contact-row");
  if (!row) return;
  event.preventDefault();
  const getsLink = row.querySelector("[data-gets-link]");
  if (getsLink) getsLink.click();
  else row.querySelector("form.contact-person")?.requestSubmit();
});

// ✨ The sidebar ("Your pathway") is a <details>, which stays open until its button is pressed again. Close it too on a
// click anywhere outside it, or on Escape, leaving the focus on its button (ticket 79). Without JavaScript only its
// button closes it. The same Escape handler closes an open lock note (ticket 97).
document.addEventListener("click", (event) => {
  document.querySelectorAll("details.pathway-nav-toggle[open]").forEach((sidebar) => {
    if (!sidebar.contains(event.target)) sidebar.open = false;
  });
});

// ✨ A lock note open on "Locked" (ticket 97) closes first, the focus staying where it is, and stays closed until the
// pointer and the focus have both left it; with none open, Escape closes the sidebar.
const OPEN_LOCK = ".lock:not(.is-dismissed):is(:hover, :focus-within)";

function reopenLeftLocks() {
  setTimeout(() => {
    document.querySelectorAll(".lock.is-dismissed").forEach((lock) => {
      if (!lock.matches(":hover, :focus-within")) lock.classList.remove("is-dismissed");
    });
  });
}

document.addEventListener("pointerout", reopenLeftLocks);
document.addEventListener("focusout", reopenLeftLocks);

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  const openLocks = document.querySelectorAll(OPEN_LOCK);
  if (openLocks.length) {
    openLocks.forEach((lock) => lock.classList.add("is-dismissed"));
    return;
  }
  const sidebar = document.querySelector("details.pathway-nav-toggle[open]");
  if (!sidebar) return;
  sidebar.open = false;
  sidebar.querySelector("summary").focus();
});

// ✨ The top bar stays in view (ticket 91), so a jump to a place on the page would land under it. Keep its height in
// --top-bar-height, which the stylesheet adds to the page's scroll padding; it changes with the demo strip, the phone's
// width and a long title wrapping. Without JavaScript the stylesheet's fallback height stands.
const topBar = document.querySelector(".top-bar");
if (topBar) {
  const keepHeight = () => document.documentElement.style.setProperty("--top-bar-height", `${topBar.offsetHeight}px`);
  keepHeight();
  if (window.ResizeObserver) new ResizeObserver(keepHeight).observe(topBar);
}

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
  // ✨ A checklist that is the first block of its page (Walk with a coach) shows the new screen from the top of the
  // page, its title included, not from the card (ticket 82).
  const opensPage = checklist.parentElement?.querySelector('[id^="block-"]') === checklist;
  if (checklist.getBoundingClientRect().top < 0) {
    if (opensPage) window.scrollTo({ top: 0 });
    else checklist.scrollIntoView({ block: "start" });
  }
  const heading = checklist.querySelector("h2");
  if (!heading || checklist.contains(document.activeElement)) return;
  heading.tabIndex = -1;
  heading.focus({ preventScroll: true });
});

// ✨ Copy an issued observer or coach link, as the prototype's Copy button does, or a group's join link. Without
// JavaScript the field is still there to select and copy by hand.
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

// ✨ A dialog in a contact list's row (a link just issued, or asking before someone is removed) shows open in the row
// without JavaScript; once it has loaded, as a modal, on the page and in each row htmx sends back (fix-2).
htmx.onLoad((content) => {
  content.querySelectorAll("dialog[data-shows-modal][open]").forEach((dialog) => {
    dialog.close();
    dialog.showModal();
  });
});

// ✨ An agreement scale shows the point chosen beside its prompt, as v3's does (fix-2); without JavaScript it shows
// once the page comes back.
document.addEventListener("change", (event) => {
  if (!event.target.matches?.(".rate input")) return;
  const shown = event.target.closest("fieldset").querySelector(".scale-val");
  shown.textContent = event.target.value;
  shown.classList.remove("unset");
});

// ✨ Demo only (fix-20): a demo-only element marked data-demo-reveal (the results page's "Retake the strengths evaluation (demo
// only)") comes `hidden`, and only a demo system's markup carries one. Option/Alt held on its own for a second shows
// it, or on a phone the element marked data-demo-reveal-hold (the page's title) pressed and held for a second; another
// key, a click, letting go early or a scroll cancels. Once shown it stays until the page is left, so the participant
// can let go and click it. On a page without one no listener is added.
(() => {
  const hidden = [...document.querySelectorAll("[data-demo-reveal]")];
  if (!hidden.length) return;
  const HOLD_MS = 1000;
  const MOVE_PX = 10;
  let timer = null;
  let start = null;
  let revealed = false;

  const cancel = () => {
    clearTimeout(timer);
    timer = null;
    start = null;
  };
  const show = (shown) => {
    revealed = shown;
    hidden.forEach((element) => (element.hidden = !shown));
  };
  const hold = () => {
    cancel();
    timer = setTimeout(() => {
      show(true);
      cancel();
    }, HOLD_MS);
  };
  const typing = (target) => target.closest?.("input, textarea, select, [contenteditable]");

  document.addEventListener("keydown", (event) => {
    if (revealed) return;
    if (event.key === "Alt" && !typing(event.target)) {
      if (!event.repeat) hold();
    } else {
      cancel();
    }
  });
  document.addEventListener("keyup", cancel);
  document.addEventListener("pointerdown", cancel);
  window.addEventListener("blur", cancel); // ✨ Alt-Tab away never sends the keyup

  const title = document.querySelector("[data-demo-reveal-hold]");
  title?.addEventListener("pointerdown", (event) => {
    if (event.pointerType !== "touch" || revealed) return;
    event.stopPropagation(); // ✨ not the document's, which would cancel the hold this starts
    hold();
    start = { x: event.clientX, y: event.clientY };
  });
  title?.addEventListener("pointermove", (event) => {
    if (start && Math.hypot(event.clientX - start.x, event.clientY - start.y) > MOVE_PX) cancel();
  });
  title?.addEventListener("pointerup", cancel);
  title?.addEventListener("pointercancel", cancel); // ✨ the browser has taken the touch to scroll
  title?.addEventListener("contextmenu", (event) => {
    if (start) event.preventDefault(); // ✨ a long press would open the menu part way through the hold
  });

  // ✨ Back to the page from the browser's cache counts as arriving again: hidden until revealed.
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) show(false);
  });
})();

// ✨ Demo only (fix-25): the demo-profile choice's "How to answer the pairs" offers only the ways of answering that
// hold with the starting profile chosen, the rest disabled, so a profile without pairs offers only "No pairs"; with
// "Sort the cards myself" nothing is offered. A choice the change disables gives way to the first one left. Without
// JavaScript every one is offered, and the server refuses one that does not fit, saying why.
(() => {
  const profile = document.querySelector("[data-demo-profile]");
  const answers = document.querySelector("[data-demo-answers]");
  if (!profile || !answers) return;
  const fit = () => {
    const options = [...answers.options];
    options.forEach((option) => (option.disabled = !option.dataset.fits.split(" ").includes(profile.value)));
    answers.disabled = options.every((option) => option.disabled);
    if (answers.selectedOptions[0]?.disabled) {
      const first = options.find((option) => !option.disabled);
      if (first) answers.value = first.value;
    }
  };
  profile.addEventListener("change", fit);
  fit();
})();

// ✨ Whether the visitor has asked their device for less motion; every movement below is skipped if so.
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// ✨ The homepage's forest moves only for those who have not asked their device for less motion. It is started here
// rather than by `autoplay`, which would play before this check could stop it; everyone else, and anyone without
// JavaScript, sees the still frame.
if (!reducedMotion) {
  document.querySelectorAll("video[data-plays-unless-reduced-motion]").forEach((video) => {
    video.play().catch(() => {}); // ✨ a browser that refuses keeps the still frame
  });
}

// ✨ Homepage: "Whatever You Do" landing view interactions.
// Each block is self-contained and no-ops when its section is absent, so the
// same bundle serves every page.

// --- Landing CTA: a brief page transition before Django takes over navigation, on the links marked for it ---
if (document.querySelector("main.page") && !reducedMotion) {
  let navigating = false;
  document.addEventListener("click", (event) => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest("a[data-page-wipe][href]");
    if (!link || link.target || link.hasAttribute("download")) return;
    const destination = new URL(link.href, window.location.href);
    if (destination.origin !== window.location.origin) return;
    if (typeof Element.prototype.animate !== "function") return;

    event.preventDefault();
    if (navigating) return;
    navigating = true;
    const wipe = document.createElement("div");
    wipe.setAttribute("aria-hidden", "true");
    wipe.dataset.pageWipeOverlay = "";
    Object.assign(wipe.style, {
      position: "fixed",
      inset: "0",
      zIndex: "9999",
      pointerEvents: "none",
      background: "var(--green-deep)",
      clipPath: `circle(0 at ${event.clientX}px ${event.clientY}px)`,
    });
    document.body.append(wipe);
    const animation = wipe.animate(
      { clipPath: [`circle(0 at ${event.clientX}px ${event.clientY}px)`, `circle(150vmax at ${event.clientX}px ${event.clientY}px)`] },
      { duration: 500, easing: "cubic-bezier(.7,0,.3,1)", fill: "forwards" },
    );
    animation.onfinish = () => window.location.assign(destination.href);
  });
  // ✨ Back restores the page from the browser's cache as it was left, overlay and all: take it away (fix-2).
  window.addEventListener("pageshow", (event) => {
    if (!event.persisted) return;
    document.querySelectorAll("[data-page-wipe-overlay]").forEach((wipe) => wipe.remove());
    navigating = false;
  });
}

// --- Evaluation tabs: auto-advancing, pausable, keyboard-navigable ---
(() => {
  const bar = document.getElementById("aTabs");
  const text = document.getElementById("aText");
  const imgs = document.getElementById("aImgs");
  const section = document.getElementById("how");
  const list = document.getElementById("aSteps");
  if (!bar || !text || !list) return;
  // ✨ The steps are written once, in the page (ticket 98); the tabs show them one at a time.
  const steps = [...list.children].map((li) => ({ title: li.querySelector("h3").textContent, summary: li.querySelector("p").textContent }));
  section?.classList.add("tabs-on");
  const STEP_MS = 7000; // ✨ how long each step shows before the next
  let i = 0, timer, start, remain = STEP_MS;
  const pauseReasons = new Set();
  bar.innerHTML = steps.map((step, j) => `<button class="tab" role="tab" id="atab${j}" aria-controls="aText" aria-selected="${j === 0}"><span class="tab-number">0${j + 1}</span><b>${step.title}</b><span class="bar"><i></i></span></button>`).join("");
  if (imgs) imgs.innerHTML = steps.map((_, j) => `<div class="tp-anim" data-i="${j}"></div>`).join("");
  const tabs = [...bar.children];
  const pics = imgs ? [...imgs.children] : [];
  bar.style.setProperty("--dur", STEP_MS + "ms");
  const render = () => {
    const step = steps[i];
    const stepText = document.createElement("div");
    stepText.className = "tp-anim";
    stepText.innerHTML = `<span class="tp-step">STEP 0${i + 1}</span><h3></h3><p></p>`;
    stepText.querySelector("h3").textContent = step.title;
    stepText.querySelector("p").textContent = step.summary;
    text.replaceChildren(stepText);
    text.setAttribute("aria-labelledby", "atab" + i);
    tabs.forEach((tab, j) => {
      tab.setAttribute("aria-selected", j === i);
      tab.classList.toggle("done", j < i);
      const fill = tab.querySelector(".bar i");
      if (fill) {
        fill.style.animation = "none";
        void fill.offsetWidth;
        fill.style.animation = "";
      }
    });
    pics.forEach((pic, j) => pic.classList.toggle("on", j === i));
    if (bar.scrollWidth > bar.clientWidth) {
      bar.scrollTo({
        left: Math.max(0, tabs[i].offsetLeft - bar.offsetLeft - 16),
        behavior: reducedMotion ? "auto" : "smooth",
      });
    }
  };
  const go = (n) => {
    i = (n + steps.length) % steps.length;
    render();
    remain = STEP_MS;
    schedule();
  };
  const schedule = () => {
    clearTimeout(timer);
    if (reducedMotion || pauseReasons.size) return;
    start = Date.now();
    timer = setTimeout(() => go(i + 1), remain);
  };
  const pause = (reason) => {
    if (pauseReasons.has(reason)) return;
    if (!pauseReasons.size) {
      clearTimeout(timer);
      remain = Math.max(0, remain - (Date.now() - start));
    }
    pauseReasons.add(reason);
    section?.classList.add("paused");
  };
  const resume = (reason) => {
    pauseReasons.delete(reason);
    if (!pauseReasons.size) {
      section?.classList.remove("paused");
      schedule();
    }
  };
  tabs.forEach((tab, j) => tab.addEventListener("click", () => go(j)));
  const prev = document.getElementById("aPrev");
  const next = document.getElementById("aNext");
  if (prev) prev.addEventListener("click", () => go(i - 1));
  if (next) next.addEventListener("click", () => go(i + 1));
  bar.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight") { go(i + 1); tabs[i].focus(); }
    if (e.key === "ArrowLeft") { go(i - 1); tabs[i].focus(); }
  });
  if (section) {
    section.addEventListener("focusin", () => pause("focus"));
    section.addEventListener("focusout", (event) => {
      if (section.contains(event.relatedTarget)) return;
      resume("focus");
    });
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) pause("visibility");
      else resume("visibility");
    });
  }
  if (reducedMotion) bar.style.setProperty("--dur", "0s");
  render();
  schedule();
})();

// --- Scroll reveal: word-by-word opacity ---
for (const el of document.querySelectorAll("#reveal, [data-reveal]")) {
  const wrap = (node) => {
    if (node.nodeType === 3) {
      const frag = document.createDocumentFragment();
      node.textContent.split(/(\s+)/).forEach((token) => {
        if (!token) return;
        if (/^\s+$/.test(token)) frag.appendChild(document.createTextNode(token));
        else {
          const span = document.createElement("span");
          span.className = "w";
          span.textContent = token;
          frag.appendChild(span);
        }
      });
      node.replaceWith(frag);
    } else if (node.nodeType === 1 && node.tagName === "EM") {
      node.classList.add("w");
    } else {
      [...node.childNodes].forEach(wrap);
    }
  };
  [...el.childNodes].forEach(wrap);
  const words = [...el.querySelectorAll(".w")];
  if (reducedMotion) {
    words.forEach((w) => w.classList.add("on"));
    continue;
  }
  const update = () => {
    const r = el.getBoundingClientRect();
    const vh = innerHeight;
    const p = Math.min(1, Math.max(0, (vh * 0.85 - r.top) / (r.height + vh * 0.35)));
    const n = Math.round(p * words.length);
    words.forEach((w, i) => w.classList.toggle("on", i < n));
  };
  addEventListener("scroll", update, { passive: true });
  addEventListener("resize", update);
  update();
}

// --- Calling ring: adapt the existing Meet cards without adding sample people or images ---
(() => {
  if (reducedMotion) return;
  let stage = document.getElementById("ringStage");
  const ring = document.getElementById("ring") ?? document.querySelector(".meet-cards");
  if (!ring) return;
  const cards = [...ring.children];
  if (cards.length < 2) return;

  if (!stage) {
    stage = document.createElement("div");
    stage.id = "ringStage";
    stage.className = "ring-stage";
    stage.setAttribute("role", "region");
    stage.setAttribute("aria-roledescription", "carousel");
    stage.setAttribute("aria-label", "People in different callings and stages of life");
    ring.before(stage);
    ring.classList.add("ring");
    stage.append(ring);
    const controls = document.createElement("div");
    controls.className = "ring-controls";
    controls.innerHTML = '<button type="button" class="ring-control" data-ring-step="-1" aria-label="Previous calling">←</button><button type="button" class="ring-control ring-toggle" data-ring-toggle></button><button type="button" class="ring-control" data-ring-step="1" aria-label="Next calling">→</button>';
    stage.append(controls);
  }

  const angle = 360 / cards.length;
  const cardInterval = 7000;
  let radius = 0;
  let rotation = 0;
  let drag;
  // ✨ Only the pause button between the arrows stops the ring (fix-17): hovering or focusing it no longer does, so it
  // never stops or starts unasked. The button's name says what pressing it will do. Reduced motion keeps the plain
  // cards, returning above before any button is made.
  let paused = false;
  const toggle = stage.querySelector("[data-ring-toggle]");
  const pauseIcon = '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" focusable="false"><rect x="3" y="2" width="3.5" height="12" rx="1" fill="currentColor"/><rect x="9.5" y="2" width="3.5" height="12" rx="1" fill="currentColor"/></svg>';
  const playIcon = '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" focusable="false"><path d="M4 2.2v11.6a.8.8 0 0 0 1.2.7l9-5.8a.8.8 0 0 0 0-1.4l-9-5.8A.8.8 0 0 0 4 2.2z" fill="currentColor"/></svg>';
  const showToggle = () => {
    if (!toggle) return;
    toggle.innerHTML = paused ? playIcon : pauseIcon;
    toggle.setAttribute("aria-label", paused ? "Play carousel" : "Pause carousel");
  };
  let lastFrame;
  let transitionUntil = 0;
  let transitionTimer;
  const layout = () => {
    const width = stage.clientWidth;
    const cardWidth = Math.min(280, Math.max(220, width * 0.55));
    radius = (cardWidth + Math.max(16, width * 0.025)) * cards.length / (2 * Math.PI);
    const controlsSpace = parseFloat(getComputedStyle(stage).getPropertyValue("--ring-controls-space")) || 0;
    stage.style.height = `${Math.max(360, Math.min(500, cardWidth * 1.35)) + controlsSpace}px`;
    cards.forEach((card, index) => {
      card.style.width = `${cardWidth}px`;
      card.style.transform = `translate(-50%, -50%) rotateY(${index * angle}deg) translateZ(${radius}px)`;
    });
  };
  const draw = () => {
    ring.style.transform = `rotateY(${rotation}deg)`;
  };
  const tick = (now) => {
    const elapsed = lastFrame === undefined ? 0 : Math.min(now - lastFrame, 64);
    lastFrame = now;
    if (!paused && !drag && now >= transitionUntil) {
      rotation -= angle * elapsed / cardInterval;
      draw();
    }
    requestAnimationFrame(tick);
  };
  stage.addEventListener("pointerdown", (event) => {
    if (event.target.closest("button")) return;
    drag = { x: event.clientX, rotation };
    stage.setPointerCapture(event.pointerId);
  });
  stage.addEventListener("pointermove", (event) => {
    if (!drag) return;
    rotation = drag.rotation + (event.clientX - drag.x) * 0.08;
    draw();
  });
  const stopDrag = () => { drag = undefined; };
  stage.addEventListener("pointerup", stopDrag);
  stage.addEventListener("pointercancel", stopDrag);
  toggle?.addEventListener("click", () => {
    paused = !paused;
    showToggle();
  });
  showToggle();
  stage.querySelectorAll("[data-ring-step]").forEach((button) => {
    button.addEventListener("click", () => {
      rotation += Number(button.dataset.ringStep) * angle;
      transitionUntil = performance.now() + 700;
      ring.style.transition = "transform 700ms cubic-bezier(.2,.7,.2,1)";
      draw();
      clearTimeout(transitionTimer);
      transitionTimer = window.setTimeout(() => { ring.style.transition = "none"; }, 750);
    });
  });
  window.addEventListener("resize", layout);
  layout();
  draw();
  requestAnimationFrame(tick);
})();

// --- Real partner marks only; omit the carousel when no partners are supplied ---
(() => {
  const row = document.getElementById("logoRow");
  if (!row) return;
  const partners = [...row.children];
  if (!partners.length) {
    row.closest(".logos")?.remove();
    return;
  }
  partners.forEach((partner) => partner.classList.add("in"));
  if (reducedMotion || partners.length <= 5) return;

  let page = 0;
  const pageCount = Math.ceil(partners.length / 5);
  const showPage = () => {
    partners.forEach((partner, index) => {
      const visible = Math.floor(index / 5) === page;
      partner.hidden = !visible;
      partner.classList.toggle("in", visible);
      partner.classList.toggle("out", !visible);
    });
  };
  showPage();
  window.setInterval(() => {
    page = (page + 1) % pageCount;
    showPage();
  }, 5000);
})();

// --- Magnetic buttons (fine pointers only) ---
// ✨ Only a pill marked data-magnetic follows the pointer: the homepage's and the hub's.
if (window.matchMedia("(hover: hover) and (pointer: fine)").matches && !reducedMotion) {
  document.addEventListener("pointermove", (event) => {
    const button = event.target.closest && event.target.closest("[data-magnetic]");
    if (button) {
      const box = button.getBoundingClientRect();
      const dx = (event.clientX - (box.left + box.width / 2)) / box.width;
      const dy = (event.clientY - (box.top + box.height / 2)) / box.height;
      button.style.transition = "transform .25s cubic-bezier(.2,.7,.2,1), filter .2s";
      button.style.transform = `translate(${(dx * 10).toFixed(1)}px,${(dy * 8).toFixed(1)}px)`;
      const arrow = button.querySelector(".pill-arrow");
      if (arrow) arrow.style.translate = `${(dx * 5).toFixed(1)}px ${(dy * 4).toFixed(1)}px`;
    }
  }, { passive: true });
  document.addEventListener("pointerout", (event) => {
    const button = event.target.closest && event.target.closest("[data-magnetic]");
    if (button && !button.contains(event.relatedTarget)) {
      button.style.transition = "transform .5s cubic-bezier(.2,.7,.2,1), filter .2s";
      button.style.transform = "";
      const arrow = button.querySelector(".pill-arrow");
      if (arrow) arrow.style.translate = "";
    }
  });
}

mountSorts();
