import typer

from . import apps, env, postgres, redis
from typing import Annotated, Optional
from heroku_audit import __version__
from rich.table import Table
from rich.console import Console
from typer.rich_utils import _print_commands_panel


app = typer.Typer(help="Heroku audit tool")


app.add_typer(apps.app)
app.add_typer(env.app)
app.add_typer(postgres.app)
app.add_typer(redis.app)


def version_callback(version: bool):
    if version:
        print("Version", __version__)
        raise typer.Exit()


def list_callback(should_list: bool):
    if should_list:
        click_command = typer.main.get_command(app)

        commands = []
        for group_name, group in sorted(click_command.commands.items()):
            for _command_name, command in sorted(group.commands.items()):
                # Prefix command name
                command.name = f"{group_name} {command.name}"
                commands.append(command)

        _print_commands_panel(
            name="Commands", commands=commands, markup_mode="rich", console=Console()
        )

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
    ] = False,
    should_list: Annotated[
        Optional[bool],
        typer.Option(
            "--list",
            "-l",
            is_eager=True,
            help="Show the available reports and then exit.",
            callback=list_callback,
        ),
    ] = False,
):
    pass
