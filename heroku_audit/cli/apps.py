import typer
from heroku_audit.client import heroku
from typing import Annotated
from rich.progress import track
from concurrent.futures import ThreadPoolExecutor
from heroku_audit.format import display_data, FormatOption, Format
from heroku_audit.utils import get_apps_for_teams
from rich.text import Text
from heroku_audit.options import TeamOption

app = typer.Typer(name="apps", help="Report on Environment variables.")


@app.command()
def formation(
    process: Annotated[str, typer.Option()] = "web",
    team: TeamOption = None,
    format: FormatOption = Format.TABLE,
):
    """
    Review formation for a given process.
    """
    with ThreadPoolExecutor() as executor:
        apps = heroku.apps() if team is None else get_apps_for_teams(team)

        app_formations = {}

        for app, formations in track(
            executor.map(lambda a: (a, a.process_formation()), apps),
            description="Loading formation...",
            total=len(apps),
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
            key=lambda r: r["App"],
        ),
        format,
    )
