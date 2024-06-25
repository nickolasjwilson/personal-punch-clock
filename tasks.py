"""In this module are Invoke <www.pyinvoke.org> tasks."""

import invoke


@invoke.task
def test(context: invoke.context.Context) -> None:
    """Runs unit tests."""
    context.run("pytest test")


@invoke.task
def check(context: invoke.context.Context) -> None:
    """Statically checks the types."""
    context.run("mypy *.py test")


@invoke.task
def format_(context: invoke.context.Context) -> None:
    """Formats the code."""
    context.run("isort *.py test")
    context.run("black *.py test")


@invoke.task
def analyze(context: invoke.context.Context) -> None:
    """Statically analyzes the code."""
    context.run("pylint *.py test")
