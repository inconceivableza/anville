// ✨ Regenerates prototype_scoring.json by running the prototype's own scoring code on fixed sorts.
//
// The item bank and computeAll() are read out of the prototype file and run as they are, so the golden
// output is what the prototype computes, not what anyone believes it computes. Run from the repository root:
//
//     node tests/core/golden/prototype_scoring.mjs
//
// Sorts are written in the prototype's own terms: its inverted bucket integers (1 is "Real strength") and
// its item ids. The Python side maps them to the new identifiers, once, where it loads this file.

import { readFileSync, writeFileSync } from "node:fs";
import vm from "node:vm";

const html = readFileSync("Prototypes for reference/original-prototype.html", "utf8");
const itemBank = html.match(/var giftItems=\[[\s\S]*?\];/)[0];
const computeAll = html.match(/function computeAll\(\)\{[\s\S]*?return s;\s*\}/)[0];

const SEEDS = { 1: 85, 2: 65, 3: 45, 4: 25, 5: 10 }; // the prototype's `dv`, fine-tune step

function score(sort) {
  const giftScores = Object.fromEntries(Object.entries(sort).map(([id, [, value]]) => [id, value]));
  const context = { saState: { giftScores } };
  vm.runInNewContext(`${itemBank}\n${computeAll}\nresult = computeAll();`, context);
  return context.result;
}

const ids = [...itemBank.matchAll(/id:'(\w+)'/g)].map((match) => match[1]);
const sortOf = (bucketAndValue) => Object.fromEntries(ids.map((id, i) => [id, bucketAndValue(id, i)]));

const cases = {
  // Each bucket in turn, sliders left at their seeds: a sort alone gives a complete result.
  "sorted-and-left-at-seeds": sortOf((id, i) => [(i % 5) + 1, SEEDS[(i % 5) + 1]]),
  // Every slider moved, to values unrelated to the buckets.
  "fine-tuned": sortOf((id, i) => [(i % 5) + 1, (i * 37 + 11) % 101]),
  // The compositional pair: these two give the same result.
  "all-strongest": sortOf(() => [1, SEEDS[1]]),
  "all-weakest": sortOf(() => [5, SEEDS[5]]),
  // Apostle and Ideate each hold exactly 0.5% (1 of 200): Math.round gives 1, where Python's round() gives 0.
  // Every other construct but two scores 0, so ties fall back to declaration order.
  "half-a-percent": sortOf((id) => (id === "a1" ? [5, 1] : id === "p1" ? [1, 199] : [5, 0])),
};

const golden = Object.entries(cases).map(([name, sort]) => ({ name, sort, prototype: score(sort) }));
writeFileSync(new URL("prototype_scoring.json", import.meta.url), JSON.stringify(golden, null, 2) + "\n");
console.log(`Wrote ${golden.length} golden cases.`);
