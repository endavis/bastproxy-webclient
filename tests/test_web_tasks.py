"""The web app's doit tasks, its CSP checks and its checks of planted violations (#7).

``tools/doit/web.py`` wraps npm scripts for the Svelte app under ``src/web/``. The wiring tests
need no Node. The planted-violation tests copy the app into ``tmp_path``, plant one violation,
and run the real npm script; they need ``src/web/node_modules`` (``doit web_install``) and skip
without it. CI installs it in the coverage job, so they run there.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar

import pytest

from tools.doit import web
from tools.doit.build import _unexpected_app_members
from tools.doit.maintenance import task_cleanup
from tools.doit.quality import (
    task_check,
    task_deadcode,
    task_format,
    task_format_check,
    task_lint,
    task_type_check,
)
from tools.doit.security import task_audit, task_licenses, task_sbom
from tools.doit.testing import task_test

REPO_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = REPO_ROOT / "src" / "web"

WEB_TASKS: dict[str, Callable[[], dict[str, Any]]] = {
    "web_install": web.task_web_install,
    "web_lint": web.task_web_lint,
    "web_format": web.task_web_format,
    "web_format_check": web.task_web_format_check,
    "web_typecheck": web.task_web_typecheck,
    "web_test": web.task_web_test,
    "web_deadcode": web.task_web_deadcode,
    "web_audit": web.task_web_audit,
    "web_licenses": web.task_web_licenses,
    "web_sbom": web.task_web_sbom,
    "web_build": web.task_web_build,
}


class TestWiring:
    """Each Python check takes in its web counterpart."""

    @pytest.mark.parametrize(
        ("task", "counterpart"),
        [
            (task_lint, "web_lint"),
            (task_format, "web_format"),
            (task_format_check, "web_format_check"),
            (task_type_check, "web_typecheck"),
            (task_deadcode, "web_deadcode"),
            (task_audit, "web_audit"),
            (task_licenses, "web_licenses"),
            (task_sbom, "web_sbom"),
            (task_test, "web_test"),
        ],
    )
    def test_python_task_depends_on_its_web_counterpart(
        self, task: Callable[[], dict[str, Any]], counterpart: str
    ) -> None:
        assert counterpart in task()["task_dep"]

    def test_check_installs_and_builds_the_web_app(self) -> None:
        deps = task_check()["task_dep"]
        assert "web_install" in deps
        assert deps.index("web_build") > deps.index("web_install")

    def test_check_still_starts_with_env_check(self) -> None:
        assert task_check()["task_dep"][0] == "env_check"

    @pytest.mark.parametrize("name", [n for n in WEB_TASKS if n != "web_install"])
    def test_every_web_task_depends_on_web_install(self, name: str) -> None:
        assert "web_install" in WEB_TASKS[name]()["task_dep"]

    def test_web_install_is_cached_on_the_manifest_and_lockfile(self) -> None:
        task = web.task_web_install()
        assert task["file_dep"] == ["src/web/package.json", "src/web/package-lock.json"]
        assert task["targets"] == ["src/web/node_modules/.package-lock.json"]
        assert any("npm" in a and " ci" in a for a in task["actions"] if isinstance(a, str))
        assert web._require_npm in task["actions"]

    @pytest.mark.parametrize("name", list(WEB_TASKS))
    def test_commands_have_no_single_quote(self, name: str) -> None:
        """cmd.exe does not read single quotes."""
        for action in WEB_TASKS[name]()["actions"]:
            if isinstance(action, str):
                assert "'" not in action

    def test_scripts_the_tasks_run_exist_in_package_json(self) -> None:
        import json

        scripts = json.loads((WEB_ROOT / "package.json").read_text(encoding="utf-8"))["scripts"]
        for name in WEB_TASKS:
            for action in WEB_TASKS[name]()["actions"]:
                if isinstance(action, str) and " run " in action:
                    assert action.split(" run ", 1)[1] in scripts

    def test_build_checks_its_output(self) -> None:
        assert WEB_TASKS["web_build"]()["actions"][-1] is web._check_build_output

    def test_cleanup_removes_the_web_build(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import inspect

        assert "src/web/dist" in inspect.getsource(task_cleanup)


class TestRequireNpm:
    def test_missing_npm_exits_with_a_hint_naming_nvmrc(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(shutil, "which", lambda _name: None)
        with pytest.raises(SystemExit) as raised:
            web._require_npm()
        assert raised.value.code == 1
        assert ".nvmrc" in capsys.readouterr().out

    def test_present_npm_passes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")
        web._require_npm()


_CLEAN_INDEX = (
    "<!doctype html><html><head><title>t</title>"
    '<script type="module" crossorigin src="./assets/index-abc.js"></script>'
    '<link rel="stylesheet" href="./assets/index-abc.css"></head>'
    '<body><div id="app"></div></body></html>'
)


class TestBuiltIndexFailures:
    def test_clean_index_has_no_failures(self) -> None:
        assert web._built_index_failures(_CLEAN_INDEX) == []

    @pytest.mark.parametrize(
        ("html", "expected"),
        [
            ("<script>alert(1)</script>", "inline <script>"),
            ("<style>body{}</style>", "<style> element"),
            ('<div style="color:red"></div>', "style attribute"),
            ('<button onclick="x()"></button>', "event handler onclick"),
            ('<script src="/assets/a.js"></script>', "not a relative URL"),
            ('<script src="//cdn.example/a.js"></script>', "not a relative URL"),
            ('<script src="http://example.com/a.js"></script>', "not a relative URL"),
            ('<script src="https://example.com/a.js"></script>', "not a relative URL"),
            ('<link rel="icon" href="data:image/png;base64,AAAA">', "not a relative URL"),
            ('<link rel="icon" href="DATA:image/png;base64,AAAA">', "not a relative URL"),
            ('<a href="javascript:void(0)">x</a>', "not a relative URL"),
        ],
    )
    def test_each_csp_violation_is_reported(self, html: str, expected: str) -> None:
        failures = web._built_index_failures(html)
        assert len(failures) == 1
        assert expected in failures[0]

    def test_every_violation_is_reported_not_just_the_first(self) -> None:
        html = '<script>x()</script><style></style><div style="a:b" onclick="y()"></div>'
        assert len(web._built_index_failures(html)) == 4


class TestBuiltDistFailures:
    def _dist(self, tmp_path: Path, index: str = _CLEAN_INDEX) -> Path:
        dist = tmp_path / "dist"
        (dist / "assets").mkdir(parents=True)
        (dist / "index.html").write_text(index, encoding="utf-8")
        return dist

    def test_missing_index_is_a_failure(self, tmp_path: Path) -> None:
        assert "was not built" in web._built_dist_failures(tmp_path / "dist")[0]

    def test_clean_build_passes(self, tmp_path: Path) -> None:
        dist = self._dist(tmp_path)
        (dist / "assets" / "index-abc.css").write_text("body{color:red}", encoding="utf-8")
        assert web._built_dist_failures(dist) == []

    def test_data_url_in_css_is_a_failure(self, tmp_path: Path) -> None:
        dist = self._dist(tmp_path)
        (dist / "assets" / "index-abc.css").write_text(
            'a{background:url("data:image/png;base64,AAAA")}', encoding="utf-8"
        )
        failures = web._built_dist_failures(dist)
        assert failures == ["index-abc.css holds a data: URL (blocked by the CSP)"]

    def test_index_failure_is_reported(self, tmp_path: Path) -> None:
        dist = self._dist(tmp_path, "<script>x()</script>")
        assert len(web._built_dist_failures(dist)) == 1


class TestCheckBuildOutput:
    def test_failure_exits_non_zero_and_names_the_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (tmp_path / "src" / "web" / "dist").mkdir(parents=True)
        (tmp_path / "src" / "web" / "dist" / "index.html").write_text(
            "<script>x()</script>", encoding="utf-8"
        )
        monkeypatch.chdir(tmp_path)
        with pytest.raises(SystemExit) as raised:
            web._check_build_output()
        assert raised.value.code == 1
        assert "inline <script>" in capsys.readouterr().out

    def test_clean_build_passes(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        dist = tmp_path / "src" / "web" / "dist"
        dist.mkdir(parents=True)
        (dist / "index.html").write_text(_CLEAN_INDEX, encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        web._check_build_output()
        assert "fits the CSP" in capsys.readouterr().out


def _wheel(path: Path, members: list[str]) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        for name in members:
            zf.writestr(name, "x")
    return path


class TestUnexpectedAppMembers:
    _GOOD: ClassVar[list[str]] = [
        "pkg/__init__.py",
        "pkg/py.typed",
        "pkg-1.0.dist-info/METADATA",
        "pkg-1.0.dist-info/RECORD",
    ]

    def test_package_only_wheel_is_clean(self, tmp_path: Path) -> None:
        assert _unexpected_app_members(_wheel(tmp_path / "a.whl", self._GOOD), "pkg") == []

    @pytest.mark.parametrize(
        "member",
        [
            "src/web/src/App.svelte",
            "web/package.json",
            "pkg/web/node_modules/x/index.js",
            "pkg/App.svelte",
            "pkg/main.ts",
            "pkg/package-lock.json",
            "other/__init__.py",
        ],
    )
    def test_app_files_are_reported(self, tmp_path: Path, member: str) -> None:
        wheel = _wheel(tmp_path / "a.whl", [*self._GOOD, member])
        assert _unexpected_app_members(wheel, "pkg") == [member]

    def test_real_wheel_config_leaves_the_app_out(self) -> None:
        import tomllib

        with (REPO_ROOT / "pyproject.toml").open("rb") as fh:
            config = tomllib.load(fh)
        assert config["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == [
            "src/bastproxy_webclient"
        ]


# --- planted violations: the real npm scripts, on a copy of the app -----------------------------

_NODE_READY = (
    shutil.which("npm") is not None and (WEB_ROOT / "node_modules" / ".package-lock.json").is_file()
)

needs_node = pytest.mark.skipif(
    not _NODE_READY or sys.platform == "win32",
    reason="needs npm and src/web/node_modules (doit web_install); the copy links node_modules, "
    "which Windows does not allow without privileges",
)


@pytest.fixture
def app(tmp_path: Path) -> Path:
    """A copy of the web app that links the real ``node_modules``."""
    target = tmp_path / "web"
    shutil.copytree(
        WEB_ROOT,
        target,
        ignore=shutil.ignore_patterns("node_modules", "dist", "coverage"),
    )
    (target / "node_modules").symlink_to(WEB_ROOT / "node_modules", target_is_directory=True)
    return target


def _npm(app: Path, script: str) -> subprocess.CompletedProcess[str]:
    npm = shutil.which("npm")
    assert npm is not None
    return subprocess.run(
        [npm, "--prefix", str(app), "run", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )


def _plant(app: Path, name: str, text: str) -> None:
    (app / "src" / name).write_text(text, encoding="utf-8")


@needs_node
class TestCleanControl:
    @pytest.mark.parametrize("script", ["lint", "format:check", "typecheck", "deadcode", "test"])
    def test_unchanged_app_passes(self, app: Path, script: str) -> None:
        result = _npm(app, script)
        assert result.returncode == 0, result.stdout + result.stderr


@needs_node
class TestPlantedViolations:
    def test_lint_error_fails_lint(self, app: Path) -> None:
        _plant(app, "bad.ts", "debugger;\nexport {};\n")
        result = _npm(app, "lint")
        assert result.returncode != 0
        assert "bad.ts" in result.stdout

    def test_unformatted_file_fails_format_check(self, app: Path) -> None:
        _plant(app, "ugly.ts", "export const   a=1\n")
        result = _npm(app, "format:check")
        assert result.returncode != 0
        assert "ugly.ts" in result.stdout + result.stderr

    def test_type_error_fails_typecheck(self, app: Path) -> None:
        _plant(app, "typed.ts", 'export const n: number = "x";\n')
        assert _npm(app, "typecheck").returncode != 0

    def test_inner_html_fails_lint(self, app: Path) -> None:
        _plant(
            app,
            "html.ts",
            "export function put(v: string): void {\n  document.body.innerHTML = v;\n}\n",
        )
        result = _npm(app, "lint")
        assert result.returncode != 0
        assert "no-unsanitized" in result.stdout

    def test_at_html_fails_lint(self, app: Path) -> None:
        (app / "src" / "Raw.svelte").write_text(
            '<script lang="ts">\n  let { value }: { value: string } = $props();\n</script>\n\n'
            "{@html value}\n",
            encoding="utf-8",
        )
        result = _npm(app, "lint")
        assert result.returncode != 0
        assert "no-at-html-tags" in result.stdout

    def test_coverage_below_threshold_fails_test(self, app: Path) -> None:
        body = "\n".join(f"  if (n === {i}) return {i};" for i in range(40))
        _plant(
            app,
            "untested.ts",
            f"export function pick(n: number): number {{\n{body}\n  return -1;\n}}\n",
        )
        result = _npm(app, "test")
        assert result.returncode != 0
        assert "threshold" in result.stdout + result.stderr

    def test_unused_export_fails_deadcode(self, app: Path) -> None:
        _plant(app, "orphan.ts", "export const orphan = 1;\n")
        result = _npm(app, "deadcode")
        assert result.returncode != 0
        assert "orphan" in result.stdout
