import { mount, unmount } from "svelte";
import { describe, expect, it } from "vitest";

import App from "./App.svelte";

describe("App", () => {
  it("renders the default title", () => {
    const target = document.createElement("div");
    const app = mount(App, { target });
    expect(target.querySelector("h1")?.textContent).toBe("bastproxy web client");
    void unmount(app);
  });

  it("renders a given title", () => {
    const target = document.createElement("div");
    const app = mount(App, { target, props: { title: "Custom" } });
    expect(target.querySelector("h1")?.textContent).toBe("Custom");
    void unmount(app);
  });
});
