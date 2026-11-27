---
title: Web client
description: The Svelte web app under src/web/, its checks, its doit tasks and the CSP its build must fit
audience:
  - contributors
tags:
  - web
  - svelte
  - ci
---

# Web client

This is a Python template project with a JavaScript app in it. The app lives in `src/web/`: Vite,
Svelte 5 and TypeScript. The Python package under `src/bastproxy_webclient/` does not import it, and
the wheel does not carry its sources. [ADR-0001](../decisions/0001-keep-the-web-app-in-srcweb-inside-the-python-template-project.md)
records the layout.

## Setup

Install the Node version in `.nvmrc` (for example `nvm install`), then:

```bash
uv run doit web_install   # npm ci, from src/web/package-lock.json
uv run doit web_build     # builds src/web/dist/ and checks it against the CSP
```

`web_install` fails, naming `.nvmrc`, when `npm` is missing. The web checks never skip quietly: a
skipped check would let `doit check` pass without checking the app.

## One check per Python check

Each web check is the counterpart of a Python one, and runs inside the matching `doit` task.

| Python | Web (`src/web/`) | Task |
| :--- | :--- | :--- |
| ruff | ESLint with `typescript-eslint` and `eslint-plugin-svelte` | `web_lint` |
| ruff format | Prettier with `prettier-plugin-svelte` | `web_format_check`, `web_format` |
| mypy | `tsc --noEmit` (strict, twice) and `svelte-check` | `web_typecheck` |
| bandit | `eslint-plugin-no-unsanitized` and `svelte/no-at-html-tags`; CodeQL `javascript-typescript` | `web_lint` |
| coverage | Vitest with `@vitest/coverage-v8`, thresholds of 90 that fail the run | `web_test` |
| vulture | knip: unused files, exports and dependencies | `web_deadcode` |
| pip-audit | `npm audit --audit-level=moderate` | `web_audit` |
| pip-licenses | `scripts/check-licenses.mjs` with an allowlist | `web_licenses` |
| cyclonedx-bom | `@cyclonedx/cyclonedx-npm`, to `tmp/sbom-web.json` | `web_sbom` |
| `wheel_check` | `vite build`, then a CSP check of the output | `web_build` |

`doit format_check`, `lint`, `type_check`, `deadcode`, `audit`, `licenses`, `sbom` and `test` depend
on their web task, so `doit check` runs them all. `doit check` also lists `web_install` and
`web_build`, which no Python task covers. The tool commands live in the `scripts` of
`src/web/package.json`; each task is `npm --prefix "src/web" run <script>`. See the
[Doit Tasks Reference](doit-tasks-reference.md#web-tasks).

## The CSP the build must fit

The proxy serves the build under a Content-Security-Policy, from a path it chooses at run time
([bastproxy ADR-0025](https://github.com/endavis/bastproxy/blob/main/docs/decisions/0025-the-web-plugin-serves-pages-and-a-client-websocket-from-one-listener-with-shared-sessions-and-data-providers.md)).
So the output must hold:

- no inline script or style, no `style=` attribute, no `on*=` handler;
- no `data:` URL (`assetsInlineLimit: 0`) and no `modulePreload` polyfill, which is inline code;
- only relative URLs (`base: "./"`): no `http(s):`, `//` or leading `/`.

`web_build` checks `dist/index.html` and the stylesheets for each of these and fails naming what it
found. The check is `_built_index_failures` in `tools/doit/web.py`.

## Licenses

`web_licenses` runs `src/web/scripts/check-licenses.mjs`, a script with no dependencies. It reads
every package in `package-lock.json` and accepts only the licenses in `ALLOWED_LICENSES` at the top
of the script (an SPDX `OR` passes if any side is allowed, `AND` needs every side). A package with a
missing or `UNKNOWN` license fails, and the script names each offender with its path, version and
license. It also accepts `MIT-0`, which `jsdom` pulls in through `@csstools/*`. Two packages are MPL-2.0, a file-level copyleft license, and both are used
at build time only: `eslint-plugin-no-unsanitized` and `lightningcss` (a dependency of Vite). Every
npm package is a `devDependency`, pinned to an exact version.

## Regenerating the lockfile

Regenerate `package-lock.json` with npm 11: `cd src/web && npx npm@11 install`. npm 9 and 10 crash
while resolving the Vitest peer dependencies. `npm ci`, which `web_install` runs, works on npm 9.

## Keeping the Python tools out of `src/web/`

`npm install` puts Python files (node-gyp) and prose under `src/web/node_modules`, and `src/` is a
scan root for the Python tools. `pyproject.toml` excludes `src/web` from ruff (also with
`force-exclude`, for pre-commit), mypy, bandit, vulture, codespell and pyright. Coverage measures
only `bastproxy_webclient` and `tools`, mutmut mutates only the package, and the wheel packages
only `src/bastproxy_webclient`. `doit wheel_check` also fails when the wheel holds web app files.
`tests/test_python_tool_excludes.py` runs each tool and confirms it skips the app.

## Tests

`tests/test_web_tasks.py` checks the wiring and the CSP check. Its planted-violation tests copy the
app, plant one violation (a lint error, an unformatted file, a type error, `innerHTML`, `{@html}`,
a file under the coverage threshold, an unused export) and run the real npm script; a clean copy is
the control. They need `src/web/node_modules` and skip without it. The CI `coverage` job installs it.

Component tests use Svelte 5 `mount` in jsdom, without `@testing-library/svelte`.
