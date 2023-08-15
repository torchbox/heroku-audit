import typer
from . import postgres, env
from typing import Annotated, Optional
from heroku_audit import __version__

app = typer.Typer(help="Heroku audit tool")

app.add_typer(postgres.app, name="postgres")
app.add_typer(env.app, name="env")


def version_callback(version: bool):
    if version:
        print("Version", __version__)
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-v",
            is_eager=True,
            help="Show the version and then exit.",
            callback=version_callback,
        ),
    ] = False
):
    pass
