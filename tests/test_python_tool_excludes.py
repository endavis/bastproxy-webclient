"""The Python tools must not scan the Svelte web app under ``src/web/`` (#7).

``src/web/`` can hold Python files (node-gyp scripts under ``node_modules``, a build helper)
and prose, and ``src/`` is a scan root for every Python tool here. Each test runs the real
tool on a scratch project that has the repository's ``pyproject.toml`` and one violation under
``src/web/`` and the same one outside it, and expects the tool to report only the one outside.
Without the second violation, a tool that found nothing at all would pass.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
INSIDE = Path("src/web/scripts")
OUTSIDE = Path("src/other")
# Built at run time, so codespell does not flag this file for the typo it plants.
TYPO = "rec" + "ieve"


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A scratch project with the repository's tool configuration."""
    shutil.copy(REPO_ROOT / "pyproject.toml", tmp_path / "pyproject.toml")
    for name in ("tests", "tools"):
        (tmp_path / name).mkdir()
    return tmp_path


def _plant(project: Path, name: str, text: str) -> None:
    """Write ``name`` with ``text`` both under ``src/web/`` and outside it."""
    for folder in (INSIDE, OUTSIDE):
        target = project / folder
        target.mkdir(parents=True, exist_ok=True)
        (target / name).write_text(text, encoding="utf-8")


def _run(project: Path, *argv: str) -> str:
    result = subprocess.run(
        [sys.executable, "-m", *argv],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    return (result.stdout + result.stderr).replace("\\", "/")


def _assert_only_outside(output: str) -> None:
    assert "src/other" in output, f"the tool missed the control violation:\n{output}"
    assert "src/web" not in output, f"the tool scanned src/web:\n{output}"


def test_ruff_skips_the_web_app(project: Path) -> None:
    _plant(project, "bad.py", "import os\n")
    _assert_only_outside(
        _run(project, "ruff", "check", "--output-format=concise", "src/", "tests/", "tools/")
    )


def test_ruff_skips_a_web_file_named_on_the_command_line(project: Path) -> None:
    """``force-exclude`` also applies to files passed explicitly, as pre-commit does."""
    _plant(project, "bad.py", "import os\n")
    output = _run(project, "ruff", "check", "--output-format=concise", str(INSIDE / "bad.py"))
    assert "src/web" not in output


def test_mypy_skips_the_web_app(project: Path) -> None:
    _plant(project, "bad.py", 'x: int = "a"\n')
    _assert_only_outside(_run(project, "mypy", "src/"))


def test_bandit_skips_the_web_app(project: Path) -> None:
    _plant(project, "bad.py", "import subprocess\nsubprocess.call('x', shell=True)\n")
    _assert_only_outside(_run(project, "bandit", "-c", "pyproject.toml", "-r", "src/"))


def test_vulture_skips_the_web_app(project: Path) -> None:
    _plant(project, "bad.py", "import os\n")
    _assert_only_outside(_run(project, "vulture"))


def test_codespell_skips_the_web_packages_and_build(project: Path) -> None:
    """The app's own sources stay spell-checked; its packages and build output do not."""
    for folder in ("src/web/node_modules/pkg", "src/web/dist", "src/web/src", "src/other"):
        (project / folder).mkdir(parents=True)
        (project / folder / "typo.md").write_text(f"This is {TYPO} typo.\n", encoding="utf-8")
    output = _run(project, "codespell_lib", "src/", "tests/", "tools/")
    assert "src/other" in output
    assert "src/web/src" in output, "the app's own sources should be spell-checked"
    assert "node_modules" not in output
    assert "src/web/dist" not in output


def test_codespell_skips_the_lockfile(project: Path) -> None:
    (project / "src/web").mkdir(parents=True)
    (project / "src/web/package-lock.json").write_text(f'{{"{TYPO}": 1}}\n', encoding="utf-8")
    assert "package-lock" not in _run(project, "codespell_lib", "src/")


def _tool(name: str) -> dict[str, Any]:
    """Return the ``[tool.<name>]`` table of the repository's ``pyproject.toml``."""
    with (REPO_ROOT / "pyproject.toml").open("rb") as fh:
        table: dict[str, Any] = tomllib.load(fh)["tool"][name]
    return table


def test_pyright_excludes_the_web_app() -> None:
    assert "src/web" in _tool("pyright")["exclude"]


def test_coverage_source_is_the_package_and_tools() -> None:
    assert _tool("coverage")["run"]["source"] == ["bastproxy_webclient", "tools"]


def test_mutmut_mutates_only_the_package() -> None:
    assert _tool("mutmut")["source_paths"] == ["src/bastproxy_webclient/"]


def test_wheel_packages_only_the_package() -> None:
    assert _tool("hatch")["build"]["targets"]["wheel"]["packages"] == ["src/bastproxy_webclient"]
