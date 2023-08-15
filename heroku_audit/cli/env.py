import typer
from heroku_audit.client import heroku
from typing import Optional, Annotated
from rich.progress import track
from concurrent.futures import ThreadPoolExecutor
from heroku_audit.format import display_data, FormatOption, Format
from heroku_audit.utils import get_apps_for_teams
from rich.text import Text

app = typer.Typer()


@app.command()
def value(
    key: Annotated[str, typer.Argument(help="Variable to audit")],
    missing: Annotated[
        Optional[bool],
        typer.Option(help="Only show apps with the variable missing"),
    ] = False,
    team: Annotated[
        Optional[str], typer.Option(help="Limit options to the given team")
    ] = None,
    format: FormatOption = Format.TABLE,
):
    """ """
    with ThreadPoolExecutor() as executor:
        apps = heroku.apps() if team is None else get_apps_for_teams(team)

        app_values = {}

        for app, config_vars in track(
            executor.map(lambda a: (a, a.config()), apps),
            description="Loading config...",
            total=len(apps),
        ):
            value = config_vars.to_dict().get(key)

            if value is not None and not missing:
                app_values[app] = value
            elif value is None:
                app_values[app] = Text("UNSET", style="red")

    display_data(
        sorted(
            ({"App": app.name, "Value": value} for app, value in app_values.items()),
            key=lambda r: r["App"],
        ),
        format,
    )
