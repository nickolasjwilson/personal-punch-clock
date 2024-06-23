"""In this module are Invoke <www.pyinvoke.org> tasks."""


import invoke


@invoke.task
def test(context: invoke.context.Context) -> None:
    context.run("pytest test", pty=True)
