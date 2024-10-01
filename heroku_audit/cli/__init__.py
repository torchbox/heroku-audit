from typing import Annotated, Optional, cast

import typer
from rich.console import Console
from typer.rich_utils import _print_commands_panel

from heroku_audit import __version__
from heroku_audit.config import APP_DIR, load_env_config

from . import apps, env, postgres, redis, users

load_env_config()

app = typer.Typer(help="Heroku audit tool")


app.add_typer(apps.app)
app.add_typer(env.app)
app.add_typer(postgres.app)
app.add_typer(redis.app)
app.add_typer(users.app)


def version_callback(version: bool) -> None:
    if version:
        print(f"Heroku Audit v{__version__}")
        raise typer.Exit()


def show_config_dir_callback(should_show_config_dir: bool) -> None:
    if should_show_config_dir:
        print(APP_DIR)
        raise typer.Exit()


def list_callback(should_list: bool) -> None:
    if should_list:
        typer_group = typer.main.get_group(app)

        commands = []
        for group_name, group in sorted(typer_group.commands.items()):
            command_group = cast(typer.core.TyperGroup, group)
            for _command_name, command in sorted(command_group.commands.items()):
                # Prefix command name
                command.name = f"{group_name} {command.name}"
                commands.append(command)
        max_cmd_len = max((len(command.name or "") for command in commands), default=0)
        _print_commands_panel(
            name="Commands",
            commands=commands,
            markup_mode="rich",
            console=Console(),
            cmd_len=max_cmd_len,
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
    show_config_dir: Annotated[
        Optional[bool],
        typer.Option(
            "--show-config-dir",
            is_eager=True,
            help="Show the config directory location.",
            callback=show_config_dir_callback,
        ),
    ] = False,
) -> None:
    pass
