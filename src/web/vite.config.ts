import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vitest/config";

// The proxy serves the build under a Content-Security-Policy and from a path chosen at run time:
// no inline scripts or styles, no data: assets, and only relative asset URLs.
export default defineConfig({
  base: "./",
  plugins: [svelte()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
    assetsInlineLimit: 0,
    cssCodeSplit: false,
    modulePreload: { polyfill: false },
  },
  // Svelte's server build has no `mount`; the component tests need its browser build.
  ...(process.env["VITEST"] ? { resolve: { conditions: ["browser"] } } : {}),
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.ts", "scripts/**/*.test.mjs"],
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,svelte}", "scripts/**/*.mjs"],
      exclude: ["src/**/*.test.ts", "scripts/**/*.test.mjs", "src/**/*.d.ts"],
      reporter: ["text"],
      thresholds: { lines: 90, functions: 90, branches: 90, statements: 90 },
    },
  },
});
