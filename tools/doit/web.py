"""Doit tasks for the Svelte web app under ``src/web/``.

Each task is a thin wrapper over an npm script in ``src/web/package.json``, so the tool commands
live in one place and the same ones run from ``npm`` and from ``doit``. Every task depends on
``web_install``, which runs ``npm ci`` and is cached by doit on the manifest and the lockfile.

Commands use double quotes only, because ``cmd.exe`` does not read single quotes.
"""

import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from doit.tools import title_with_actions
from rich.console import Console

from .base import verbatim

WEB_DIR = "src/web"
_NODE_MODULES_MARKER = f"{WEB_DIR}/node_modules/.package-lock.json"
_URL_ATTRIBUTES = frozenset({"src", "href", "action", "poster", "srcset"})
_BLOCKED_URL_PREFIXES = ("http:", "https:", "data:", "javascript:", "//", "/")


def _require_npm() -> None:
    """Fail with a hint naming ``.nvmrc`` when ``npm`` is not on the path.

    The web checks never skip quietly: a missing Node would let ``doit check`` pass without
    checking the web app.
    """
    if shutil.which("npm") is None:
        console = Console()
        console.print(
            "[bold red]npm was not found.[/bold red] The web app needs Node: install the "
            "version in .nvmrc (for example with `nvm install`) and run the task again."
        )
        sys.exit(1)


def _npm_run(script: str) -> str:
    """Return the command that runs the npm script ``script`` in ``src/web/``."""
    return f'npm --prefix "{WEB_DIR}" run {script}'


def _web_task(script: str) -> dict[str, Any]:
    """Return the task body that runs ``script`` after ``web_install``."""
    return {
        "actions": [_npm_run(script)],
        "task_dep": ["web_install"],
        "title": title_with_actions,
        "verbosity": 2,
    }


class _IndexAuditor(HTMLParser):
    """Collect what in ``index.html`` the proxy's Content-Security-Policy would block."""

    def __init__(self) -> None:
        super().__init__()
        self.failures: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Flag inline scripts and styles, event handlers and non-relative URLs."""
        names = {name for name, _ in attrs}
        if tag == "script" and "src" not in names:
            self.failures.append("inline <script> (an inline script is blocked by the CSP)")
        if tag == "style":
            self.failures.append("<style> element (an inline style is blocked by the CSP)")
        for name, value in attrs:
            if name == "style":
                self.failures.append(f"style attribute on <{tag}> (blocked by the CSP)")
            elif name.startswith("on"):
                self.failures.append(f"event handler {name}= on <{tag}> (blocked by the CSP)")
            elif name in _URL_ATTRIBUTES and value is not None:
                self._check_url(tag, name, value.strip())

    def _check_url(self, tag: str, name: str, value: str) -> None:
        """Flag a URL that is absolute, protocol-relative, root-relative or a ``data:`` URL."""
        if value.lower().startswith(_BLOCKED_URL_PREFIXES):
            self.failures.append(
                f"{name}={value!r} on <{tag}> is not a relative URL (the build is served from "
                "a path chosen at run time)"
            )


def _built_index_failures(index_html: str) -> list[str]:
    """Return what in the built ``index.html`` breaks the proxy's CSP, empty when it fits.

    The page must hold no inline script or style, no event-handler or ``style`` attribute, and
    only relative asset URLs (``./assets/...``): no ``data:``, ``http(s):``, ``//`` or ``/``.
    """
    auditor = _IndexAuditor()
    auditor.feed(index_html)
    auditor.close()
    return auditor.failures


def _built_css_failures(css_path: Path) -> list[str]:
    """Return a failure for each ``data:`` URL in the built stylesheet ``css_path``."""
    text = css_path.read_text(encoding="utf-8")
    if "url(data:" in text.replace(" ", "").replace('"', "").replace("'", ""):
        return [f"{css_path.name} holds a data: URL (blocked by the CSP)"]
    return []


def _built_dist_failures(dist: Path) -> list[str]:
    """Return every CSP failure in the build output ``dist``, empty when it fits."""
    index = dist / "index.html"
    if not index.is_file():
        return [f"{index} was not built"]
    failures = _built_index_failures(index.read_text(encoding="utf-8"))
    for css_path in sorted(dist.rglob("*.css")):
        failures.extend(_built_css_failures(css_path))
    return failures


def _check_build_output() -> None:
    """Exit non-zero, naming each failure, when the built app does not fit the CSP."""
    failures = _built_dist_failures(Path(WEB_DIR) / "dist")
    console = Console()
    if failures:
        console.print()
        console.print("[bold red]web_build output does not fit the CSP:[/bold red]")
        for failure in failures:
            console.print("[red]-[/red]", verbatim(failure))
        sys.exit(1)
    console.print("[bold green]✓ web build fits the CSP.[/bold green]")


def task_web_install() -> dict[str, Any]:
    """Install the web app's npm dependencies from the lockfile (``npm ci``)."""
    return {
        "actions": [_require_npm, f'npm --prefix "{WEB_DIR}" ci'],
        "file_dep": [f"{WEB_DIR}/package.json", f"{WEB_DIR}/package-lock.json"],
        "targets": [_NODE_MODULES_MARKER],
        "title": title_with_actions,
        "verbosity": 2,
    }


def task_web_lint() -> dict[str, Any]:
    """Lint the web app with ESLint (also bans innerHTML and {@html})."""
    return _web_task("lint")


def task_web_format() -> dict[str, Any]:
    """Format the web app with Prettier."""
    return _web_task("format")


def task_web_format_check() -> dict[str, Any]:
    """Check the web app's formatting without changing files."""
    return _web_task("format:check")


def task_web_typecheck() -> dict[str, Any]:
    """Type-check the web app with tsc (strict) and svelte-check."""
    return _web_task("typecheck")


def task_web_test() -> dict[str, Any]:
    """Run the web app's tests with Vitest, with a coverage threshold."""
    return _web_task("test")


def task_web_deadcode() -> dict[str, Any]:
    """Find unused files, exports and dependencies in the web app with knip."""
    return _web_task("deadcode")


def task_web_audit() -> dict[str, Any]:
    """Audit the web app's npm dependencies for known vulnerabilities (moderate and above)."""
    return {
        "actions": [f'npm --prefix "{WEB_DIR}" audit --audit-level=moderate'],
        "task_dep": ["web_install"],
        "title": title_with_actions,
        "verbosity": 2,
    }


def task_web_licenses() -> dict[str, Any]:
    """Check the web app's npm licenses against the allowlist."""
    return _web_task("licenses")


def task_web_sbom() -> dict[str, Any]:
    """Generate the web app's SBOM in CycloneDX format at ``tmp/sbom-web.json``."""

    def make_tmp_dir() -> None:
        Path("tmp").mkdir(parents=True, exist_ok=True)

    task = _web_task("sbom")
    task["actions"] = [make_tmp_dir, *task["actions"]]
    return task


def task_web_build() -> dict[str, Any]:
    """Build the web app into ``src/web/dist`` and check the output fits the proxy's CSP."""
    task = _web_task("build")
    task["actions"] = [*task["actions"], _check_build_output]
    return task
