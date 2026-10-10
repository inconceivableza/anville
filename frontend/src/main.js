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
  let i = 0, timer, start, remain = DUR, paused = false;
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
    if (bar.scrollWidth > bar.clientWidth) bar.scrollTo({ left: Math.max(0, tabs[i].offsetLeft - bar.offsetLeft - 16), behavior: "smooth" });
  };
  const go = (n) => {
    i = (n + T.length) % T.length;
    render();
    remain = DUR;
    schedule();
  };
  const schedule = () => {
    clearTimeout(timer);
    if (reducedMotion || paused) return;
    start = Date.now();
    timer = setTimeout(() => go(i + 1), remain);
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
    section.addEventListener("mouseenter", () => {
      paused = true;
      section.classList.add("paused");
      clearTimeout(timer);
      remain -= Date.now() - start;
    });
    section.addEventListener("mouseleave", () => {
      paused = false;
      section.classList.remove("paused");
      schedule();
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
  addEventListener("scroll", update, { passive: true });
  addEventListener("resize", update);
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

// --- Hero logo carousel (placeholder partner marks) ---
(() => {
  const row = document.getElementById("logoRow");
  if (!row) return;
  const G = {
    circle: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3.5" fill="currentColor"/></svg>',
    cross: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="10" y="2" width="4" height="20" rx="1"/><rect x="4" y="7" width="16" height="4" rx="1"/></svg>',
    flame: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2c1 4 6 6 6 12a6 6 0 0 1-12 0c0-3 2-5 3-6 0 2 1 3 2 3 0-4-1-6 1-9z"/></svg>',
    vine: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 22V9M12 13c-4 0-6-2-6-6 4 0 6 2 6 6zM12 9c0-4 2-6 6-6 0 4-2 6-6 6z"/></svg>',
    arch: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 22V11a8 8 0 0 1 16 0v11M9 22v-7a3 3 0 0 1 6 0v7"/></svg>',
    wave: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M2 9c3-3 5 3 8 0s5 3 8 0 3-1 4-1M2 15c3-3 5 3 8 0s5 3 8 0 3-1 4-1"/></svg>',
    lamp: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3h8l2 5H6zM7 8h10v9a5 5 0 0 1-10 0z"/><path d="M12 12v4"/></svg>',
    sheaf: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 22V6M12 10l-5-5M12 10l5-5M12 15l-6-4M12 15l6-4"/></svg>',
    stone: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 20 8 4h8l5 16z" opacity=".35"/><path d="M3 20 8 4l4 16z"/></svg>',
    oak: '<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="9" r="7"/><rect x="11" y="14" width="2" height="8"/></svg>',
  };
  const L = [
    ["circle", "f-serif", "St Brendan’s"], ["cross", "f-caps", "Hope City"], ["flame", "f-light", "kinship"], ["arch", "f-serif", "Northfield Chapel"], ["vine", "f-ital", "The Vine"],
    ["wave", "f-caps", "Riverside"], ["lamp", "f-mono", "Lantern Trust"], ["sheaf", "f-serif", "Harvest Church"], ["stone", "f-caps", "Cornerstone"], ["oak", "f-light", "ember&oak"],
  ];
  let set = 0;
  const render = () => {
    row.innerHTML = L.slice(set * 5, set * 5 + 5).map(([g, f, n]) => `<span class="lg ${f}">${G[g]}<span>${n}</span></span>`).join("");
    [...row.children].forEach((el, i) => setTimeout(() => el.classList.add("in"), reducedMotion ? 0 : 100 + i * 70));
  };
  render();
  if (!reducedMotion) {
    setInterval(() => {
      [...row.children].forEach((el, i) => setTimeout(() => { el.classList.remove("in"); el.classList.add("out"); }, i * 50));
      setTimeout(() => { set = (set + 1) % 2; render(); }, 5 * 50 + 850);
    }, 4500);
  }
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
