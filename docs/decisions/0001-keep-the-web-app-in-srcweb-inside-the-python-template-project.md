---
title: "ADR-0001: Keep the web app in src/web inside the Python template project"
description: The Svelte web app lives in src/web/ inside the Python template project, with one check per Python check and a CSP check on its build.
date: 2026-11-27
audience:
  - contributors
tags:
  - adr
---

# ADR-0001: Keep the web app in src/web inside the Python template project

## Status

Accepted

## Decision

The web client is a Vite, Svelte 5 and TypeScript app in `src/web/`, inside the Python template project. The Python package (`src/bastproxy_webclient/`) and the app share one repository, one `doit check` and one CI run, and nothing else.

- **Layout.** The app is a sibling of the package under `src/`. The wheel packages only `src/bastproxy_webclient`, so the app's sources and `node_modules` never ship in it. A later issue (#8) adds the built bundle to the wheel.
- **One check per Python check.** ESLint, Prettier, `tsc` with `svelte-check`, Vitest with coverage thresholds, knip, `npm audit`, an npm license allowlist and an npm SBOM mirror ruff, ruff format, mypy, coverage, vulture, pip-audit, pip-licenses and cyclonedx-bom. Each runs inside the Python task it mirrors, so `doit check` covers the app. `web_install` and `web_build` are listed in `doit check` themselves.
- **npm scripts hold the commands.** Each `web_*` doit task is a thin `npm --prefix "src/web" run <script>` wrapper in `tools/doit/web.py`. `web_install` runs `npm ci` and is cached on `package.json` and `package-lock.json`.
- **Node is required.** A missing `npm` fails `web_install` with a hint naming `.nvmrc`; it never skips quietly. CI and the daily check set up Node from `.nvmrc`.
- **The Python tools stop at `src/web/`.** ruff, mypy, bandit, vulture, codespell and pyright exclude it; coverage and mutmut are limited to the package. Tests run each tool and confirm the exclude holds.
- **The build must fit the proxy's CSP.** The proxy serves the app under a Content-Security-Policy from a path it chooses at run time (bastproxy ADR-0025). The Vite config uses a relative `base`, no inlined assets and no module-preload polyfill, and `web_build` fails when `dist/` holds an inline script or style, an event handler, a `data:` URL or a non-relative URL.
- **Licenses.** Every npm package is a pinned `devDependency`. `web_licenses` runs a dependency-free script, `src/web/scripts/check-licenses.mjs`, that enforces an explicit allowlist over `package-lock.json`. It includes MPL-2.0 and MIT-0 (`jsdom`'s `@csstools/*`), because `eslint-plugin-no-unsanitized` and `lightningcss` carry it; both run at build time only.

## Rationale

A separate repository for the app would split one product across two sets of checks, CI and release steps, and the proxy's plugin would still have to learn which build matches which client. Keeping the app in this repository keeps one gate, and the template's tooling (doit, CI, the AI agent workflows) covers it from the first commit.

Placing it in `src/web/` keeps `src/` the place for code that ships, and the excludes keep the Python tools from reading a tree they cannot parse. Mirroring each Python check makes "the app is checked like the package" a table a reviewer can read, and gives a planted violation in each check a test.

Failing on a missing Node, instead of skipping, keeps a green `doit check` meaning that the whole project was checked. The CSP check on the build catches the one class of failure the app's own tests cannot: output that is correct but that the proxy's policy would block.

## Related Issues

- Issue #7: add the Svelte web app under `src/web/` with doit tasks and CI

## Related Documentation

- [Web client](../development/web-client.md)
- [Doit Tasks Reference](../development/doit-tasks-reference.md#web-tasks)
- [CI/CD and Testing](../development/ci-cd-testing.md#pipeline-jobs)
- [bastproxy ADR-0025](https://github.com/endavis/bastproxy/blob/main/docs/decisions/0025-the-web-plugin-serves-pages-and-a-client-websocket-from-one-listener-with-shared-sessions-and-data-providers.md)
