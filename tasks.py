"""In this module are Invoke <www.pyinvoke.org> tasks."""

import invoke

_ALL_PY_FILES = "*.py test"


@invoke.task
def test(context: invoke.context.Context) -> None:
    """Runs unit tests."""
    context.run("pytest --cov-report term-missing --cov=punch_clock test")


@invoke.task
def check(context: invoke.context.Context) -> None:
    """Statically checks the types."""
    context.run(f"mypy {_ALL_PY_FILES}")


@invoke.task
def format_(context: invoke.context.Context) -> None:
    """Formats the code."""
    context.run(f"isort {_ALL_PY_FILES}")
    context.run(f"black {_ALL_PY_FILES}")


@invoke.task
def analyze(context: invoke.context.Context) -> None:
    """Statically analyzes the code."""
    context.run(f"pylint {_ALL_PY_FILES}")
