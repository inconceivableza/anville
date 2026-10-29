// Copyright (C) New Community Church SE London 2026.
// For licensing information see ../../LICENSE.md

// ✨ The sort assessment: every item sorted into a bucket one card at a time, then fine-tuned with a slider
// seeded by its bucket. An observer may send before fine-tuning, and a document may skip fine-tuning for everyone,
// each card then sent at its bucket's seed. The server hands over the items and the buckets (weakest first) as JSON beside the
// form. The widget's only output is the form's hidden `value`, the whole sort as JSON; the server never
// trusts it, and checks and scores it on submit. Nothing is kept before then, so a reload starts the sort
// again, as in the prototype. Card order is shuffled per visit and not recorded (see the spec's open items).
//
// Where some items reword others (twins), the sort runs in two rounds, as in the two-round prototype: the originals,
// a look at how the buckets were used, then the rewordings. A participant whose sort skips fine-tuning then gets the
// prototype's quick check: the pairs answered furthest apart, to change if they look wrong.
//
// The widget's own wording ("Sort your strengths", "Not me", …) comes with the items, in the reader's wording: an
// observer's is about the participant, in the third person.

const FLY_MS = 320;
const CHOSEN_MS = 200; // ✨ How long the chosen bucket shows as chosen where the card does not fly.
const BUCKET_TONES = 5; // ✨ The stylesheet colours bucket-1 (weakest) to bucket-5 (strongest).
const GRADES = 7; // ✨ And grades the buckets' buttons, the graph's bars and the quick check's dots grade-0 to grade-6.
// ✨ The prototype's: none of round 2's first 8 cards rewords one of round 1's last 8.
const APART = 8;
// ✨ The prototype's quick check: at most 5 pairs, each answered at least 4 buckets apart, biggest gap first.
const CHECK_GAP = 4;
const MOST_CHECKS = 5;
// ✨ How much of the progress bar placing every card fills; fine-tuning, a quicker look over, is the rest.
const SORTED_PERCENT = 80;

export function mountSorts() {
  document.querySelectorAll("form[data-sort]").forEach(mountSort);
}

function mountSort(form) {
  // ✨ `placed` comes only with a demo profile, on a development or demo system (fix-23): each item's bucket and value,
  // so the sort opens with every card already placed and fine-tuning's sliders already set. The participant still
  // sends it themselves. Everyone else gets none and starts from a full deck.
  const { items, buckets, wording, fine_tunes, sends_before_fine_tuning, quick_check, placed = {} } = JSON.parse(
    document.getElementById(form.dataset.sort).textContent,
  );
  const stage = form.querySelector(".sort-stage");
  const announcer = form.querySelector("[data-sort-announcer]");
  const progress = form.querySelector(".sort-progress");
  const bucketOf = (item) => buckets.find((bucket) => bucket.id === placed[item.id]?.bucket);
  const deck = dealt(items).filter((item) => !bucketOf(item)); // ✨ Still to sort; the first is the card on show.
  const sortedPercent = fine_tunes ? SORTED_PERCENT : 100;
  // ✨ Every placement, { item, bucket }, in the order made, so undo can go all the way back.
  const history = items.filter(bucketOf).map((item) => ({ item, bucket: bucketOf(item) }));
  const twoRounds = items.some((item) => item.round === 2);
  let flying = false;
  let onRound2 = false; // ✨ Whether round 2 has been started from the halfway screen, and not undone back into round 1.
  let checks = null; // ✨ The quick check's pairs, each [round 1's placement, round 2's], once every card is placed.

  const inBucket = (bucket) => history.filter((placed) => placed.bucket === bucket).map((placed) => placed.item);
  const strongestFirst = () => buckets.map((bucket, index) => [bucket, index]).reverse();

  // ✨ The weakest bucket takes the first tone and the strongest the last, however many buckets there are.
  const tone = (index) =>
    `bucket-${buckets.length === 1 ? BUCKET_TONES : Math.round((index * (BUCKET_TONES - 1)) / (buckets.length - 1)) + 1}`;
  const grade = (index) =>
    `grade-${buckets.length === 1 ? GRADES - 1 : Math.round((index * (GRADES - 1)) / (buckets.length - 1))}`;

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
    if (deck.length === 0) return quickCheck() ?? allSorted();
    if (twoRounds && deck[0].round === 2 && !onRound2) return halfway();
    // ✨ In two rounds, counted within the round on show.
    const round = deck[0].round;
    const dealing = twoRounds ? items.filter((item) => item.round === round) : items;
    const done = dealing.length - deck.filter((item) => dealing.includes(item)).length;
    announcer.textContent = `Card ${done + 1} of ${dealing.length}: ${deck[0].text}`;
    return [
      twoRounds
        ? stepHeader(`Round ${round} of 2 · ${wording[`round_${round}_title`]}`, wording.sort_heading)
        : stepHeader(fine_tunes && "Step 1 of 2 — Sort", wording.sort_heading),
      el(
        "div",
        { class: "card-area" },
        el(
          "p",
          { class: "sort-topline" },
          twoRounds
            ? el("span", { class: "card-counter" }, el("strong", {}, done + 1), ` of ${dealing.length}`)
            : el("span", { class: "card-counter" }, el("strong", {}, done + 1), `/${items.length}`),
          el("span", { class: "sort-instruction" }, wording.sort_instruction),
        ),
        el("div", { class: "sort-deck" }, el("p", { class: "sort-card" }, deck[0].text)),
        el(
          "div",
          { class: "bucket-buttons", role: "group", "aria-label": "Buckets" },
          ...buckets.map((bucket, index) =>
            on(
              el(
                "button",
                { type: "button", class: `bucket-btn ${grade(index)}`, "data-focus": `bucket-${bucket.id}` },
                ...(index < 9 ? [el("span", { class: "bucket-key", "aria-hidden": "true" }, index + 1)] : []),
                el("span", {}, bucket.label),
              ),
              "click",
              () => sortInto(bucket, index),
            ),
          ),
        ),
        el(
          "p",
          { class: "scale-ends", "aria-hidden": "true" },
          el("span", {}, wording.scale_less),
          el("span", {}, wording.scale_more),
        ),
        el(
          "div",
          { class: "sort-foot" },
          undoButton(),
          el("span", { class: "sort-hint" }, `Tip: press 1–${Math.min(buckets.length, 9)}`),
        ),
      ),
    ];
  }

  // ✨ Between the rounds: how round 1's cards were spread over the buckets, praised where well spread, 5 or more of 7
  // buckets used and none holding more than a third of the cards, so a reader who used only a few can spread round 2's
  // more.
  function halfway() {
    announcer.textContent = "";
    const counts = buckets.map(
      (bucket) => history.filter((placed) => placed.bucket === bucket && placed.item.round === 1).length,
    );
    const most = Math.max(...counts, 1);
    const cards = counts.reduce((sum, count) => sum + count, 0);
    const fullest = counts.indexOf(most);
    const crowded = most > cards / 3;
    const spread = counts.filter(Boolean).length;
    const used = (spread >= buckets.length - 2 && !crowded ? wording.buckets_spread_well : wording.buckets_spread_more)
      .replaceAll(
        "{crowded}",
        crowded
          ? wording.buckets_crowded
              .replaceAll("{count}", most)
              .replaceAll("{cards}", cards)
              .replaceAll("{bucket}", buckets[fullest].label)
          : "",
      )
      .replaceAll("{used}", spread)
      .replaceAll("{buckets}", buckets.length);
    return [
      stepHeader("Halfway", wording.halfway_heading, wording.halfway_intro),
      el(
        "section",
        { class: "sort-graph" },
        el("h3", {}, wording.buckets_used_heading),
        el("p", {}, used),
        columns(
          el(
            "div",
            {
              class: "graph-bars",
              role: "img",
              "aria-label": buckets.map((bucket, index) => `${bucket.label}: ${counts[index]}`).join(", "),
            },
            ...counts.map((count, index) => {
              const bar = el("i", {});
              bar.style.height = `${Math.round((count / most) * 64)}px`;
              return el("div", { class: `graph-bar ${grade(index)}` }, el("b", {}, count), bar);
            }),
          ),
        ),
        columns(
          el(
            "div",
            { class: "graph-labels", "aria-hidden": "true" },
            ...buckets.map((bucket) => el("span", {}, bucket.label)),
          ),
        ),
      ),
      el(
        "div",
        { class: "sort-row-actions" },
        on(
          el("button", { type: "button", class: "pill", "data-focus": "start-round-2" }, wording.start_round_2_label),
          "click",
          () => {
            onRound2 = true;
            render(sorting);
          },
        ),
        on(
          el("button", { type: "button", class: "undo-btn", "data-focus": "undo" }, wording.undo_last_card_label),
          "click",
          undo,
        ),
      ),
    ];
  }

  // ✨ The quick check, or none where there is nothing to check.
  function quickCheck() {
    if (!quick_check) return null;
    checks ??= pairsToCheck();
    return checks.length > 0 ? checking() : null;
  }

  function pairsToCheck() {
    const placements = Object.fromEntries(history.map((placed) => [placed.item.id, placed]));
    const at = (placed) => buckets.indexOf(placed.bucket);
    return history
      .filter((placed) => placed.item.round === 2 && placements[placed.item.twin])
      .map((placed) => [placements[placed.item.twin], placed])
      .map((pair) => ({ pair, gap: Math.abs(at(pair[0]) - at(pair[1])) }))
      .filter(({ gap }) => gap >= CHECK_GAP)
      .sort((a, b) => b.gap - a.gap)
      .slice(0, MOST_CHECKS)
      .map(({ pair }) => pair);
  }

  // ✨ A changed answer changes the placement itself, so what is sent is the changed sort.
  function checking() {
    announcer.textContent = "";
    const pairs = checks.length === 1 ? "One pair" : `${checks.length} pairs`;
    return [
      stepHeader("Quick check", wording.check_heading.replaceAll("{pairs}", pairs), wording.check_intro),
      ...checks.map((pair, index) =>
        el(
          "fieldset",
          { class: "check-pair" },
          el("legend", {}, `Pair ${index + 1} of ${checks.length}`),
          ...pair.map(checkRow),
        ),
      ),
      sendButton(),
    ];
  }

  function checkRow(placement) {
    const id = `${form.dataset.sort}-check-${placement.item.id}`;
    return el(
      "div",
      { class: "check-row" },
      el(
        "p",
        { class: "check-text", id },
        el("span", { class: "check-round" }, `Round ${placement.item.round}`),
        placement.item.text,
      ),
      el("p", { class: "check-answer" }, "Your answer: ", el("strong", {}, placement.bucket.label)),
      columns(
        el(
          "div",
          { class: "check-dots", role: "radiogroup", "aria-labelledby": id },
          ...buckets.map((bucket, index) =>
            on(
              el("button", {
                type: "button",
                role: "radio",
                class: `check-dot ${grade(index)}`,
                "aria-checked": String(bucket === placement.bucket),
                "aria-label": bucket.label,
                title: bucket.label,
                "data-focus": `dot-${placement.item.id}-${bucket.id}`,
              }),
              "click",
              () => {
                placement.bucket = bucket;
                render(sorting);
              },
            ),
          ),
        ),
      ),
      el(
        "p",
        { class: "check-scale", "aria-hidden": "true" },
        el("span", {}, buckets[0].label),
        el("span", {}, buckets.at(-1).label),
      ),
    );
  }

  // ✨ A grid as many columns wide as there are buckets, set through the element's style, not a style attribute.
  function columns(element) {
    element.style.setProperty("--columns", buckets.length);
    return element;
  }

  // ✨ The chosen bucket is marked while the card goes, by mouse or key alike; with reduced motion the card stays put,
  // but the mark still shows for a moment.
  function sortInto(bucket, index) {
    if (flying || deck.length === 0) return;
    history.push({ item: deck.shift(), bucket });
    flying = true;
    stage.querySelectorAll(".bucket-btn")[index].classList.add("chosen");
    const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!still) stage.querySelector(".sort-card").classList.add(flight(index));
    setTimeout(
      () => {
        flying = false;
        render(sorting);
      },
      still ? CHOSEN_MS : FLY_MS,
    );
  }

  // ✨ Undoing round 1's last card, from the halfway screen or round 2's first card, goes back into round 1.
  function undo() {
    if (flying || history.length === 0) return;
    const { item } = history.pop();
    deck.unshift(item);
    if (item.round !== 2) onRound2 = false;
    checks = null;
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
      stepHeader(fine_tunes && "Step 1 of 2 — Sort", wording.sort_heading),
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
      stepHeader("Step 2 of 2 — Fine-tune", wording.fine_tune_heading, wording.fine_tune_intro),
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

  // ✨ The prototype's keys: 1 for the weakest bucket upwards, while the buckets are on show, but not while typing
  // elsewhere on the page or with a modifier held, so the browser's own shortcuts still work. A key press hides the
  // hover tint until the mouse moves, so the bucket under a still pointer never looks like the one chosen.
  document.addEventListener("keydown", (event) => {
    if (event.metaKey || event.ctrlKey || event.altKey || !/^[1-9]$/.test(event.key)) return;
    if (event.target.closest?.("input, select, textarea, [contenteditable]")) return;
    const button = stage.querySelectorAll(".bucket-btn")[Number(event.key) - 1];
    if (!button) return;
    event.preventDefault();
    stage.classList.add("keyed");
    button.click();
  });
  stage.addEventListener("mousemove", (event) => {
    if (event.movementX || event.movementY) stage.classList.remove("keyed");
  });
  render(sorting);
}

// ✨ With no badge (a sort that skips fine-tuning, in one round, has only the one step), none shown.
function stepHeader(badge, title, intro) {
  return el(
    "header",
    { class: "section-header" },
    ...(badge ? [el("p", { class: "step-badge" }, badge)] : []),
    el("h2", { tabindex: -1, "data-focus-start": true }, title),
    ...(intro ? [el("p", {}, intro)] : []),
  );
}

// ✨ The prototype's dealing: round 1 shuffled, then round 2 shuffled again until none of its first cards rewords one
// of round 1's last, so a card and its rewording are never close. Most shuffles of 36 pass at once; a deck that
// cannot be dealt so is dealt as last shuffled. Without rewordings, the one round, shuffled.
function dealt(items) {
  const first = shuffled(items.filter((item) => item.round !== 2));
  const second = items.filter((item) => item.round === 2);
  const last = new Set(first.slice(-APART).map((item) => item.id));
  const close = (deck) => deck.slice(0, APART).some((item) => last.has(item.twin));
  let deck = shuffled(second);
  for (let tries = 1; tries < 500 && close(deck); tries++) deck = shuffled(second);
  return [...first, ...deck];
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
