import operator
from concurrent.futures import ThreadPoolExecutor
from typing import Annotated

import typer
from rich.progress import track
from rich.text import Text

from heroku_audit.client import heroku
from heroku_audit.format import Format, FormatOption, display_data
from heroku_audit.options import TeamOption
from heroku_audit.utils import SHOW_PROGRESS, get_apps_for_teams, zip_map

app = typer.Typer(name="apps", help="Report on Heroku apps.")


@app.command()
def formation(
    process: Annotated[str, typer.Option()] = "web",
    team: TeamOption = None,
    display_format: FormatOption = Format.TABLE,
) -> None:
    """
    Review formation for a given process.
    """
    with ThreadPoolExecutor() as executor:
        apps = heroku.apps() if team is None else get_apps_for_teams(team)

        app_formations = {}

        for app, formations in track(
            zip_map(executor, lambda a: a.process_formation(), apps),
            description="Loading formation...",
            total=len(apps),
            disable=not SHOW_PROGRESS,
        ):
            target_formation = next(
                (formation for formation in formations if formation.type == process),
                None,
            )

            if target_formation is not None:
                app_formations[app] = target_formation

    display_data(
        sorted(
            (
                {
                    "App": app.name,
                    "Size": Text(formation.size, style="purple")
                    if formation.size == "Basic"
                    else formation.size,
                    "Quantity": formation.quantity
                    if formation.quantity
                    else Text("Stopped", style="red"),
                    "Command": Text(formation.command, style="green"),
                }
                for app, formation in app_formations.items()
            ),
            key=operator.itemgetter("App"),
        ),
        display_format,
    )
