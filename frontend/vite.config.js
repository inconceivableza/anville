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