import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

describe("main", () => {
  beforeEach(() => {
    vi.resetModules();
    document.body.innerHTML = "";
  });

  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("mounts the app into #app", async () => {
    document.body.innerHTML = '<div id="app"></div>';
    await import("./main");
    expect(document.querySelector("#app h1")?.textContent).toBe("bastproxy web client");
  });

  it("throws when the page has no #app element", async () => {
    await expect(import("./main")).rejects.toThrow("#app");
  });
});
