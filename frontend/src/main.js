import htmx from "htmx.org";

// ✨ Defence in depth: htmx may not run code from hx-* attributes. See ADR 0006 before changing.
htmx.config.allowEval = false;
window.htmx = htmx;
document.documentElement.dataset.javascript = "loaded";