// Copyright (C) New Community Church SE London 2026.
// For licensing information see ../LICENSE.md

import { defineConfig } from "vite";

export default defineConfig({
  base: "/static/",
  build: {
    manifest: "manifest.json",
    outDir: "dist",
    rolldownOptions: {
      input: "src/main.js",
    },
  },
});