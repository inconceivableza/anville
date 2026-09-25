// ✨ The sort assessment: every item sorted into a bucket one card at a time, then fine-tuned with a slider
// seeded by its bucket. The server hands over the items and the buckets (weakest first) as JSON beside the
// form. The widget's only output is the form's hidden `value`, the whole sort as JSON; the server never
// trusts it, and checks and scores it on submit. Nothing is kept before then, so a reload starts the sort
// again, as in the prototype. Card order is shuffled per visit and not recorded (see the spec's open items).
//
// The widget's own wording ("Sort your strengths", "Not me", …) is written here for now. The observer's sort
// (ticket 15) needs it in the third person, which is when it should move into the pathway document.

const FLY_MS = 320;
const BUCKET_TONES = 5; // ✨ The stylesheet colours bucket-1 (weakest) to bucket-5 (strongest).

export function mountSorts() {
  document.querySelectorAll("form[data-sort]").forEach(mountSort);
}

function mountSort(form) {
  const { items, buckets } = JSON.parse(document.getElementById(form.dataset.sort).textContent);
  const stage = form.querySelector(".sort-stage");
  const announcer = form.querySelector("[data-sort-announcer]");
  const deck = shuffled(items); // ✨ Still to sort; the first is the card on show.
  const history = []; // ✨ Every placement, { item, bucket }, in the order made, so undo can go all the way back.
  let flying = false;

  const inBucket = (bucket) => history.filter((placed) => placed.bucket === bucket).map((placed) => placed.item);
  const strongestFirst = () => buckets.map((bucket, index) => [bucket, index]).reverse();

  // ✨ The weakest bucket takes the first tone and the strongest the last, however many buckets there are.
  const tone = (index) =>
    `bucket-${buckets.length === 1 ? BUCKET_TONES : Math.round((index * (BUCKET_TONES - 1)) / (buckets.length - 1)) + 1}`;

  // ✨ The prototype's direction: weaker buckets fly left, stronger fly right, the middle one drops.
  const flight = (index) => {
    const middle = (buckets.length - 1) / 2;
    return index < middle ? "fly-left" : index > middle ? "fly-right" : "fly-down";
  };

  // ✨ Each screen is rebuilt whole. Keyboard focus stays on the control it was on, or moves to the new
  // screen's heading, but never jumps into the widget from elsewhere on the page.
  function render(screen) {
    const hadFocus = stage.contains(document.activeElement);
    const focused = document.activeElement?.dataset?.focus;
    stage.replaceChildren(...screen());
    if (!hadFocus) return;
    (stage.querySelector(`[data-focus="${focused}"]`) ?? stage.querySelector("[data-focus-start]"))?.focus();
  }

  function sorting() {
    if (deck.length === 0) return allSorted();
    const done = items.length - deck.length;
    announcer.textContent = `Card ${done + 1} of ${items.length}: ${deck[0].text}`;
    return [
      stepHeader(1, "Sort", "Sort your strengths"),
      el(
        "div",
        { class: "card-area" },
        el(
          "p",
          { class: "sort-topline" },
          el("span", { class: "card-counter" }, el("strong", {}, done + 1), `/${items.length}`),
          el("span", { class: "sort-instruction" }, "Choose the bucket that fits best"),
        ),
        el("p", { class: "sort-card" }, deck[0].text),
        el(
          "div",
          { class: "bucket-buttons", role: "group", "aria-label": "Buckets" },
          ...buckets.map((bucket, index) =>
            on(
              el(
                "button",
                { type: "button", class: `bucket-btn ${tone(index)}`, "data-focus": `bucket-${bucket.id}` },
                el("span", { class: "bucket-count" }, inBucket(bucket).length),
                bucket.label,
              ),
              "click",
              () => sortInto(bucket, index),
            ),
          ),
        ),
        undoButton(),
      ),
    ];
  }

  function sortInto(bucket, index) {
    if (flying || deck.length === 0) return;
    history.push({ item: deck.shift(), bucket });
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return render(sorting);
    flying = true;
    stage.querySelector(".sort-card").classList.add(flight(index));
    setTimeout(() => {
      flying = false;
      render(sorting);
    }, FLY_MS);
  }

  function undo() {
    if (flying || history.length === 0) return;
    deck.unshift(history.pop().item);
    render(sorting);
  }

  function undoButton() {
    return on(
      el(
        "button",
        { type: "button", class: "undo-btn", disabled: history.length === 0, "data-focus": "undo" },
        "↩ Undo last",
      ),
      "click",
      undo,
    );
  }

  function allSorted() {
    announcer.textContent = `All ${items.length} sorted.`;
    return [
      stepHeader(1, "Sort", "Sort your strengths"),
      el(
        "div",
        { class: "sort-done" },
        el("p", { class: "sort-done-mark", "aria-hidden": "true" }, "✅"),
        el("h3", {}, `All ${items.length} sorted!`),
        el(
          "ul",
          { class: "sort-done-counts" },
          ...strongestFirst().map(([bucket, index]) =>
            el(
              "li",
              {},
              el("span", { class: `bucket-name ${tone(index)}` }, bucket.label),
              el("strong", {}, inBucket(bucket).length),
            ),
          ),
        ),
        on(
          el("button", { type: "button", class: "btn btn-primary", "data-focus": "continue" }, "Continue to fine-tuning →"),
          "click",
          () => {
            render(fineTuning);
            writeAnswer();
          },
        ),
        undoButton(),
      ),
    ];
  }

  function fineTuning() {
    announcer.textContent = "";
    return [
      stepHeader(2, "Fine-tune", "How strong is each one?", "Grouped by how you sorted them. Adjust the sliders to fine-tune."),
      ...strongestFirst()
        .filter(([bucket]) => inBucket(bucket).length > 0)
        .map(([bucket, index]) =>
          el(
            "section",
            { class: "score-group" },
            el("h3", { class: `bucket-heading ${tone(index)}` }, `${bucket.label} (${inBucket(bucket).length})`),
            el("div", { class: "score-section" }, ...inBucket(bucket).map((item) => slider(item, bucket))),
          ),
        ),
      el("button", { type: "submit", class: "btn btn-primary btn-full sort-submit" }, "See my results →"),
    ];
  }

  function slider(item, bucket) {
    const id = `${form.dataset.sort}-${item.id}`;
    return el(
      "div",
      { class: "score-row" },
      el("label", { class: "score-label", for: id }, item.text),
      el(
        "div",
        { class: "score-scale" },
        el("span", { "aria-hidden": "true" }, "Not me"),
        el("input", {
          type: "range",
          id,
          class: "score-slider",
          min: 0,
          max: 100,
          step: 1,
          value: bucket.seed,
          "data-item": item.id,
          "data-bucket": bucket.id,
        }),
        el("span", { "aria-hidden": "true" }, "Real strength"),
      ),
    );
  }

  // ✨ The one answer: every slider's item, its bucket and its value, untouched sliders keeping their seed.
  function writeAnswer() {
    const sort = {};
    for (const slider of stage.querySelectorAll(".score-slider")) {
      sort[slider.dataset.item] = { bucket: slider.dataset.bucket, value: Number(slider.value) };
    }
    form.querySelector('input[name="value"]').value = JSON.stringify(sort);
  }

  form.addEventListener("input", (event) => {
    if (event.target.matches(".score-slider")) writeAnswer();
  });
  render(sorting);
}

function stepHeader(step, name, title, intro) {
  return el(
    "header",
    { class: "section-header" },
    el("p", { class: "step-badge" }, `Step ${step} of 2 — ${name}`),
    el("h2", { tabindex: -1, "data-focus-start": true }, title),
    ...(intro ? [el("p", {}, intro)] : []),
  );
}

// ✨ Fisher–Yates over a copy, unseeded, as the prototype's was.
function shuffled(items) {
  const deck = [...items];
  for (let i = deck.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [deck[i], deck[j]] = [deck[j], deck[i]];
  }
  return deck;
}

// ✨ Elements are built from text nodes, never innerHTML, so authored text can never become markup.
function el(tag, attributes, ...children) {
  const element = document.createElement(tag);
  for (const [name, value] of Object.entries(attributes)) {
    if (value === false) continue;
    element.setAttribute(name, value === true ? "" : value);
  }
  element.append(...children);
  return element;
}

function on(element, type, listener) {
  element.addEventListener(type, listener);
  return element;
}
