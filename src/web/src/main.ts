import { mount } from "svelte";

import App from "./App.svelte";

const target = document.getElementById("app");

if (!target) {
  throw new Error("The page has no #app element to mount the web client into.");
}

const app = mount(App, { target });

export default app;
