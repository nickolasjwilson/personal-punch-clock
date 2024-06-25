"""In this module are Invoke <www.pyinvoke.org> tasks."""

import invoke


@invoke.task
def check(context: invoke.context.Context) -> None:
    context.run("mypy *.py test")


@invoke.task
def format(context: invoke.context.Context) -> None:
    context.run("isort *.py test")
    context.run("black *.py test")


@invoke.task
def test(context: invoke.context.Context) -> None:
    context.run("pytest test")
