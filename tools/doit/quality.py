"""Code quality-related doit tasks."""

from typing import Any

from doit.tools import title_with_actions

from .base import optional_root_dirs, optional_root_files, success_message


def task_lint() -> dict[str, Any]:
    """Run ruff linting."""
    extras = optional_root_files("bootstrap.py") + optional_root_dirs("examples")
    return {
        "actions": ["uv run ruff check --output-format=concise src/ tests/ tools/" + extras],
        "task_dep": ["web_lint"],
        "title": title_with_actions,
        "verbosity": 0,
    }


def task_format() -> dict[str, Any]:
    """Format code with ruff."""
    extras = optional_root_files("bootstrap.py") + optional_root_dirs("examples")
    return {
        "actions": [
            "uv run ruff format src/ tests/ tools/" + extras,
            "uv run ruff check --fix src/ tests/ tools/" + extras,
        ],
        "task_dep": ["web_format"],
        "title": title_with_actions,
    }


def task_format_check() -> dict[str, Any]:
    """Check code formatting without modifying files."""
    extras = optional_root_files("bootstrap.py") + optional_root_dirs("examples")
    return {
        "actions": ["uv run ruff format --check src/ tests/ tools/" + extras],
        "task_dep": ["web_format_check"],
        "title": title_with_actions,
        "verbosity": 0,
    }


def task_type_check() -> dict[str, Any]:
    """Run mypy type checking (uses pyproject.toml configuration)."""
    # Covers tools/ and tests/, not just tools/doit/: narrower scopes let real
    # errors in tools/hooks/ and tests/ pass a green `doit check`. See #700.
    return {
        "actions": ["uv run mypy src/ tools/ tests/" + optional_root_files("bootstrap.py")],
        "task_dep": ["web_typecheck"],
        "title": title_with_actions,
        "verbosity": 0,
    }


def task_deadcode() -> dict[str, Any]:
    """Detect dead code with vulture (uses pyproject.toml configuration)."""
    return {
        "actions": ["uv run vulture"],
        "task_dep": ["web_deadcode"],
        "title": title_with_actions,
    }


def task_complexity() -> dict[str, Any]:
    """Analyze cyclomatic complexity with radon (A-F grades, A is best)."""
    return {
        "actions": ['uv run radon cc src/ -a -s -e "src/web/*"'],
        "title": title_with_actions,
    }


def task_maintainability() -> dict[str, Any]:
    """Analyze maintainability index with radon (A-F grades, A is best)."""
    return {
        "actions": ['uv run radon mi src/ -s -e "src/web/*"'],
        "title": title_with_actions,
    }


def task_check() -> dict[str, Any]:
    """Run all checks (format, lint, type, dead code, security, audit, spell, wheel, docs, test).

    The web app's counterparts run inside the matching Python task: ``format_check``, ``lint``,
    ``type_check``, ``deadcode``, ``audit`` and ``test`` each depend on their ``web_*`` task.
    ``web_install`` and ``web_build`` are listed here because no Python task has them as a
    counterpart; ``web_build`` also checks the build against the proxy's CSP.

    ``env_check`` runs first (#1033): it warns, without failing, when the
    environment has drifted from ``uv.lock``, replacing the
    ``post-merge``/``post-checkout`` pre-commit hooks that used to auto-sync
    on checkout.
    """
    return {
        "actions": [success_message],
        "task_dep": [
            "env_check",
            "format_check",
            "lint",
            "type_check",
            "deadcode",
            "security",
            "audit",
            "spell_check",
            "wheel_check",
            "docs_build",
            "test",
            "web_install",
            "web_build",
        ],
        "title": title_with_actions,
    }
