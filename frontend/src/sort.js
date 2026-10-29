// Copyright (C) New Community Church SE London 2026.
// For licensing information see ../../LICENSE.md

// ✨ The sort assessment: every item sorted into a bucket one card at a time, then fine-tuned with a slider
// seeded by its bucket. An observer may send before fine-tuning, and a document may skip fine-tuning for everyone,
// each card then sent at its bucket's seed. The server hands over the items and the buckets (weakest first) as JSON beside the
// form. The widget's only output is the form's hidden `value`, the whole sort as JSON; the server never
// trusts it, and checks and scores it on submit. Nothing is kept before then, so a reload starts the sort
// again, as in the prototype. Card order is shuffled per visit and not recorded (see the spec's open items), and a card
// is never dealt straight after its twin, the same card reworded.
//
// The widget's own wording ("Sort your strengths", "Not me", …) comes with the items, in the reader's wording: an
// observer's is about the participant, in the third person.

const FLY_MS = 320;
const BUCKET_TONES = 5; // ✨ The stylesheet colours bucket-1 (weakest) to bucket-5 (strongest).
// ✨ How much of the progress bar placing every card fills; fine-tuning, a quicker look over, is the rest.
const SORTED_PERCENT = 80;

export function mountSorts() {
  document.querySelectorAll("form[data-sort]").forEach(mountSort);
}

function mountSort(form) {
  // ✨ `placed` comes only with a demo profile, on a development or demo system (fix-23): each item's bucket and value,
  // so the sort opens with every card already placed and fine-tuning's sliders already set. The participant still
  // sends it themselves. Everyone else gets none and starts from a full deck.
  const { items, buckets, wording, fine_tunes, sends_before_fine_tuning, placed = {} } = JSON.parse(
    document.getElementById(form.dataset.sort).textContent,
  );
  const stage = form.querySelector(".sort-stage");
  const announcer = form.querySelector("[data-sort-announcer]");
  const progress = form.querySelector(".sort-progress");
  const bucketOf = (item) => buckets.find((bucket) => bucket.id === placed[item.id]?.bucket);
  const deck = dealt(items.filter((item) => !bucketOf(item))); // ✨ Still to sort; the first is the card on show.
  const sortedPercent = fine_tunes ? SORTED_PERCENT : 100;
  // ✨ Every placement, { item, bucket }, in the order made, so undo can go all the way back.
  const history = items.filter(bucketOf).map((item) => ({ item, bucket: bucketOf(item) }));
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
  // screen's heading when that control is gone or disabled (undo, once there is nothing left to undo), but
  // never jumps into the widget from elsewhere on the page.
  //
  // The progress bar is set here and nowhere else, from what has been done, so it moves back only on an undo.
  // The prototype set it from two places with figures that disagreed, and it jumped backwards.
  function render(screen) {
    const hadFocus = stage.contains(document.activeElement);
    const focused = document.activeElement?.dataset?.focus;
    stage.replaceChildren(...screen());
    progress.value =
      screen === fineTuning ? sortedPercent : Math.round((history.length / items.length) * sortedPercent);
    if (!hadFocus) return;
    const same = stage.querySelector(`[data-focus="${focused}"]:not(:disabled)`);
    (same ?? stage.querySelector("[data-focus-start]")).focus();
  }

  function sorting() {
    if (deck.length === 0) return allSorted();
    const done = items.length - deck.length;
    announcer.textContent = `Card ${done + 1} of ${items.length}: ${deck[0].text}`;
    return [
      stepHeader(fine_tunes && 1, "Sort", wording.sort_heading),
      el(
        "div",
        { class: "card-area" },
        el(
          "p",
          { class: "sort-topline" },
          el("span", { class: "card-counter" }, el("strong", {}, done + 1), `/${items.length}`),
          el("span", { class: "sort-instruction" }, wording.sort_instruction),
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
      stepHeader(fine_tunes && 1, "Sort", wording.sort_heading),
      el(
        "div",
        { class: "sort-done" },
        el("p", { class: "sort-done-mark", "aria-hidden": "true" }, "✅"),
        el("h3", {}, wording.all_sorted.replaceAll("{count}", items.length)),
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
        ...(fine_tunes && sends_before_fine_tuning
          ? [el("p", { class: "sort-done-choice" }, wording.send_or_fine_tune)]
          : []),
        el(
          "div",
          { class: "sort-done-actions" },
          ...(fine_tunes ? [fineTuneButton()] : [sendButton()]),
          ...(fine_tunes && sends_before_fine_tuning ? [sendNowButton()] : []),
        ),
        undoButton(),
      ),
    ];
  }

  function fineTuneButton() {
    return on(
      el("button", { type: "button", class: "pill", "data-focus": "continue" }, wording.fine_tune_label),
      "click",
      () => {
        render(fineTuning);
        writeAnswer();
      },
    );
  }

  // ✨ An observer may send as soon as every card is placed. Only the buckets are sent: the server gives each item its
  // bucket's seed, exactly as an untouched slider would have kept it. Fine-tuning stays the default, the green button,
  // so this one is a quiet link beneath it.
  function sendNowButton() {
    return on(
      el("button", { type: "submit", class: "sort-skip sort-submit", "data-focus": "send" }, wording.send_now_label),
      "click",
      writeBuckets,
    );
  }

  // ✨ Where the document skips fine-tuning, the one way on: sending the buckets, for everyone.
  function sendButton() {
    return on(
      el("button", { type: "submit", class: "pill sort-submit", "data-focus": "send" }, wording.submit_label),
      "click",
      writeBuckets,
    );
  }

  function writeBuckets() {
    const sort = Object.fromEntries(history.map(({ item, bucket }) => [item.id, { bucket: bucket.id }]));
    form.querySelector('input[name="value"]').value = JSON.stringify(sort);
  }

  function fineTuning() {
    announcer.textContent = "";
    return [
      stepHeader(2, "Fine-tune", wording.fine_tune_heading, wording.fine_tune_intro),
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
      el("button", { type: "submit", class: "pill full sort-submit" }, wording.submit_label),
    ];
  }

  // ✨ A slider starts at its bucket's seed, or at a demo profile's value while the item is still in the profile's bucket.
  function slider(item, bucket) {
    const id = `${form.dataset.sort}-${item.id}`;
    const value = placed[item.id]?.bucket === bucket.id ? placed[item.id].value : bucket.seed;
    return el(
      "div",
      { class: "score-row" },
      el("label", { class: "score-label", for: id }, item.text),
      el(
        "div",
        { class: "score-scale" },
        el("span", { "aria-hidden": "true" }, wording.slider_min),
        el("input", {
          type: "range",
          id,
          class: "score-slider",
          min: 0,
          max: 100,
          step: 1,
          value,
          "data-item": item.id,
          "data-bucket": bucket.id,
        }),
        el("span", { "aria-hidden": "true" }, wording.slider_max),
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

// ✨ With no step (a sort that skips fine-tuning has only the one), no step badge.
function stepHeader(step, name, title, intro) {
  return el(
    "header",
    { class: "section-header" },
    ...(step ? [el("p", { class: "step-badge" }, `Step ${step} of 2 — ${name}`)] : []),
    el("h2", { tabindex: -1, "data-focus-start": true }, title),
    ...(intro ? [el("p", {}, intro)] : []),
  );
}

// ✨ Shuffled again until no card is straight after its twin. Most shuffles of 72 cards in 36 twins have at least one
// pair side by side, but about one in three has none, so a few tries do; a deck that cannot be dealt so (two cards,
// twins) is dealt as last shuffled.
function dealt(items) {
  const apart = (deck) => deck.every((item, i) => i === 0 || deck[i - 1].twin !== item.id);
  let deck = shuffled(items);
  for (let tries = 1; tries < 1000 && !apart(deck); tries++) deck = shuffled(items);
  return deck;
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
