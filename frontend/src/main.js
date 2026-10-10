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

// ✨ The onboarding sliders update their visible value without owning the form state or submission.
document.addEventListener("input", (event) => {
  const slider = event.target.closest("[data-onboarding-slider]");
  if (!slider) return;
  const output = document.querySelector(`output[for="${CSS.escape(slider.id)}"]`);
  if (output) output.value = slider.value;
  slider.setAttribute("aria-valuetext", `${slider.value} out of 10`);
});

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

// ✨ The homepage's forest moves only for those who have not asked their device for less motion. It is started here
// rather than by `autoplay`, which would play before this check could stop it; everyone else, and anyone without
// JavaScript, sees the still frame.
if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
  document.querySelectorAll("video[data-plays-unless-reduced-motion]").forEach((video) => {
    video.play().catch(() => {}); // ✨ a browser that refuses keeps the still frame
  });
}

// ✨ Homepage: "Whatever You Do" landing view interactions.
// Each block is self-contained and no-ops when its section is absent, so the
// same bundle serves every page. Motion is skipped for reduced-motion users.
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// --- Landing CTA: a brief page transition before Django takes over navigation ---
if (document.querySelector("main.page") && !reducedMotion) {
  let navigating = false;
  document.addEventListener("click", (event) => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest("a.pill[href]");
    if (!link || link.target || link.hasAttribute("download")) return;
    const destination = new URL(link.href, window.location.href);
    if (destination.origin !== window.location.origin || !["/accounts/signup/", "/hub/"].includes(destination.pathname)) return;
    if (typeof Element.prototype.animate !== "function") return;

    event.preventDefault();
    if (navigating) return;
    navigating = true;
    const wipe = document.createElement("div");
    wipe.setAttribute("aria-hidden", "true");
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
}

// --- Assessment tabs: auto-advancing, pausable, keyboard-navigable ---
(() => {
  const bar = document.getElementById("aTabs");
  const text = document.getElementById("aText");
  const imgs = document.getElementById("aImgs");
  const section = document.getElementById("journey");
  if (!bar || !text) return;
  const T = [
    ["Gifts & talents", "Discover how you’ve been designed, through your eyes and those who know you.", ["36-statement strengths sort", "Romans 12 and 1 Corinthians 12", "Your results beside your friends’"], "Your strengths, as you and others see them"],
    ["The shape of your life", "Map your story and spot the moments you felt most alive.", ["An interactive life timeline", "Prompts for each chapter", "Reflection questions"], "A life timeline"],
    ["Putting your calling into words", "Put what you’ve learned into a short calling statement.", ["Draft a calling statement", "Explore possible directions", "Write up your best options"], "A calling statement and options"],
    ["Walking it out in obedience", "Turn what you’ve found into practical next steps.", ["Skills and experience to grow", "A step-by-step roadmap", "Check-ins with your mentor"], "A roadmap for the year ahead"],
    ["Letter to your future self", "Capture what you’ve heard, to read again when it matters.", ["A guided letter", "Sent back to you later", "Your baseline answers revisited"], "A letter, sent back to you later"],
  ];
  const DUR = 7000;
  let i = 0, timer, start, remain = DUR;
  const pauseReasons = new Set();
  bar.innerHTML = T.map((t, j) => `<button class="tab" role="tab" id="atab${j}" aria-controls="aText" aria-selected="${j === 0}"><span class="n">0${j + 1}</span><b>${t[0]}</b><span class="bar"><i></i></span></button>`).join("");
  if (imgs) imgs.innerHTML = T.map((t, j) => `<div class="tp-anim" data-i="${j}"></div>`).join("");
  const tabs = [...bar.children];
  const pics = imgs ? [...imgs.children] : [];
  bar.style.setProperty("--dur", DUR + "ms");
  const render = () => {
    const t = T[i];
    text.innerHTML = `<div class="tp-anim"><span class="n">SECTION 0${i + 1}</span><h3>${t[0]}</h3><p>${t[1]}</p></div><ul class="tp-anim">${t[2].map((x) => `<li><svg><use href="#leaf"/></svg>${x}</li>`).join("")}</ul>`;
    text.setAttribute("aria-labelledby", "atab" + i);
    tabs.forEach((b, j) => {
      b.setAttribute("aria-selected", j === i);
      b.classList.toggle("done", j < i);
      const bi = b.querySelector(".bar i");
      if (bi) {
        bi.style.animation = "none";
        void bi.offsetWidth;
        bi.style.animation = "";
      }
    });
    pics.forEach((im, j) => im.classList.toggle("on", j === i));
    if (bar.scrollWidth > bar.clientWidth) {
      bar.scrollTo({
        left: Math.max(0, tabs[i].offsetLeft - bar.offsetLeft - 16),
        behavior: reducedMotion ? "auto" : "smooth",
      });
    }
  };
  const go = (n) => {
    i = (n + T.length) % T.length;
    render();
    remain = DUR;
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
  tabs.forEach((b, j) => b.addEventListener("click", () => go(j)));
  const prev = document.getElementById("aPrev");
  const next = document.getElementById("aNext");
  if (prev) prev.addEventListener("click", () => go(i - 1));
  if (next) next.addEventListener("click", () => go(i + 1));
  bar.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight") { go(i + 1); tabs[i].focus(); }
    if (e.key === "ArrowLeft") { go(i - 1); tabs[i].focus(); }
  });
  if (section) {
    section.addEventListener("mouseenter", () => pause("pointer"));
    section.addEventListener("mouseleave", () => resume("pointer"));
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

// --- How it works: sticky scrollytelling ---
(() => {
  const steps = [...document.querySelectorAll(".how-step")];
  const panels = [...document.querySelectorAll(".how-bg-panel")];
  const dots = [...document.querySelectorAll("#howDots i")];
  if (!steps.length) return;
  let cur = 0;
  const set = (i) => {
    if (i === cur) return;
    cur = i;
    panels.forEach((p, j) => p.classList.toggle("on", j === i));
    dots.forEach((d, j) => d.classList.toggle("on", j === i));
    steps.forEach((st, j) => st.classList.toggle("on", j === i));
  };
  const update = () => {
    const mid = innerHeight / 2;
    let best = 0, bestDist = 1e9;
    steps.forEach((st, j) => {
      const r = st.getBoundingClientRect();
      const d = Math.abs(r.top + r.height / 2 - mid);
      if (d < bestDist) { bestDist = d; best = j; }
    });
    set(best);
  };
  if (!reducedMotion) {
    addEventListener("scroll", update, { passive: true });
    addEventListener("resize", update);
  }
  update();
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
    controls.innerHTML = '<button type="button" class="ring-control" data-ring-step="-1" aria-label="Previous calling">←</button><button type="button" class="ring-control" data-ring-toggle aria-label="Pause carousel">Pause</button><button type="button" class="ring-control" data-ring-step="1" aria-label="Next calling">→</button>';
    stage.append(controls);
  }

  const angle = 360 / cards.length;
  const cardInterval = 7000;
  let radius = 0;
  let rotation = 0;
  let drag;
  let pausedByUser = false;
  let interactionPaused = false;
  let lastFrame;
  let transitionUntil = 0;
  let transitionTimer;
  const toggle = stage.querySelector("[data-ring-toggle]");
  const layout = () => {
    const width = stage.clientWidth;
    const cardWidth = Math.min(280, Math.max(220, width * 0.55));
    radius = (cardWidth + Math.max(16, width * 0.025)) * cards.length / (2 * Math.PI);
    stage.style.height = `${Math.max(360, Math.min(500, cardWidth * 1.35))}px`;
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
    if (!pausedByUser && !interactionPaused && !drag && now >= transitionUntil) {
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
  stage.addEventListener("pointerenter", () => { interactionPaused = true; });
  stage.addEventListener("pointerleave", () => { interactionPaused = false; });
  stage.addEventListener("focusin", () => { interactionPaused = true; });
  stage.addEventListener("focusout", (event) => {
    if (!stage.contains(event.relatedTarget)) interactionPaused = false;
  });
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
  toggle?.addEventListener("click", () => {
    pausedByUser = !pausedByUser;
    toggle.textContent = pausedByUser ? "Resume" : "Pause";
    toggle.setAttribute("aria-label", pausedByUser ? "Resume carousel" : "Pause carousel");
  });
  window.addEventListener("resize", layout);
  layout();
  draw();
  requestAnimationFrame(tick);
})();

// --- Count up only real values supplied by the page; never manufacture impact figures ---
(() => {
  const stats = [...document.querySelectorAll(".stat[data-v]")];
  if (!stats.length) return;
  const show = (stat, animate) => {
    const target = Number(stat.dataset.v);
    const value = stat.querySelector(".num b");
    const bar = stat.querySelector(".bar i");
    if (!Number.isFinite(target) || !value) return;
    if (bar) bar.style.width = `${Math.max(0, Math.min(100, target))}%`;
    if (!animate) {
      value.textContent = String(target);
      return;
    }
    const started = performance.now();
    const frame = (now) => {
      const progress = Math.min(1, (now - started) / 1600);
      value.textContent = String(Math.round(target * (1 - (1 - progress) ** 3)));
      if (progress < 1) requestAnimationFrame(frame);
    };
    requestAnimationFrame(frame);
  };
  if (reducedMotion || !("IntersectionObserver" in window)) {
    stats.forEach((stat) => show(stat, false));
    return;
  }
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      show(entry.target, true);
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.4 });
  stats.forEach((stat) => observer.observe(stat));
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
if (window.matchMedia("(hover: hover) and (pointer: fine)").matches && !reducedMotion) {
  document.addEventListener("pointermove", (e) => {
    const b = e.target.closest && e.target.closest(".pill");
    if (b) {
      const r = b.getBoundingClientRect();
      const dx = (e.clientX - (r.left + r.width / 2)) / r.width;
      const dy = (e.clientY - (r.top + r.height / 2)) / r.height;
      b.style.transition = "transform .25s cubic-bezier(.2,.7,.2,1), filter .2s";
      b.style.transform = `translate(${(dx * 10).toFixed(1)}px,${(dy * 8).toFixed(1)}px)`;
      const a = b.querySelector(".ar");
      if (a) a.style.translate = `${(dx * 5).toFixed(1)}px ${(dy * 4).toFixed(1)}px`;
    }
  }, { passive: true });
  document.addEventListener("pointerout", (e) => {
    const b = e.target.closest && e.target.closest(".pill");
    if (b && !b.contains(e.relatedTarget)) {
      b.style.transition = "transform .5s cubic-bezier(.2,.7,.2,1), filter .2s";
      b.style.transform = "";
      const a = b.querySelector(".ar");
      if (a) a.style.translate = "";
    }
  });
}

mountSorts();
