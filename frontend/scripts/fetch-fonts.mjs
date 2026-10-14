// Copyright (C) New Community Church SE London 2026.
// For licensing information see ../../LICENSE.md

// ✨ Switzer comes from Fontshare under the ITF Free Font License, which lets us serve it from our own site but not
// make the files available through a public repository, so they are never committed (ticket 48). This fetches the
// three weights the stylesheet uses from Fontshare's own kit, unchanged, before every build. Files already present are
// kept, so a build works offline once they have been fetched; a build without them fails rather than quietly falling
// back to a system font.

import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const KIT = "https://api.fontshare.com/v2/fonts/download/switzer";
const IN_KIT = "Switzer_Complete/Fonts/WEB/fonts";
const WEIGHTS = ["Switzer-Regular.woff2", "Switzer-Medium.woff2", "Switzer-Semibold.woff2"];
const FONTS = join(dirname(fileURLToPath(import.meta.url)), "..", "fonts");

if (WEIGHTS.every((name) => existsSync(join(FONTS, name)))) {
  process.exit(0);
}

const response = await fetch(KIT);
if (!response.ok) {
  console.error(`Could not fetch Switzer from Fontshare (${response.status}); the build needs it.`);
  process.exit(1);
}

const scratch = mkdtempSync(join(tmpdir(), "switzer-"));
try {
  const zip = join(scratch, "switzer.zip");
  writeFileSync(zip, Buffer.from(await response.arrayBuffer()));
  mkdirSync(FONTS, { recursive: true });
  execFileSync("unzip", ["-o", "-j", zip, ...WEIGHTS.map((name) => `${IN_KIT}/${name}`), "-d", FONTS], {
    stdio: "ignore",
  });
} finally {
  rmSync(scratch, { recursive: true, force: true });
}

const missing = WEIGHTS.filter((name) => !existsSync(join(FONTS, name)));
if (missing.length) {
  console.error(`Fontshare's kit did not hold ${missing.join(", ")}.`);
  process.exit(1);
}
