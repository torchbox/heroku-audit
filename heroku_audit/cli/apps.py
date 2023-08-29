import operator
from concurrent.futures import ThreadPoolExecutor
from typing import Annotated

import typer
from rich.progress import track
from rich.text import Text

from heroku_audit.client import heroku
from heroku_audit.format import Format, FormatOption, display_data
from heroku_audit.options import TeamOption
from heroku_audit.style import style_dyno_formation_quantity, style_dyno_formation_size
from heroku_audit.utils import (
    SHOW_PROGRESS,
    get_addon_plan,
    get_addons,
    get_apps_for_teams,
    zip_map,
)

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
                    "Size": style_dyno_formation_size(formation.size),
                    "Quantity": style_dyno_formation_quantity(formation.quantity),
                    "Command": Text(formation.command, style="green"),
                }
                for app, formation in app_formations.items()
            ),
            key=operator.itemgetter("App"),
        ),
        display_format,
    )


@app.command()
def addon(
    addon_name: Annotated[
        str, typer.Argument(help="Addon name (prefix) to search for")
    ],
    team: TeamOption = None,
    display_format: FormatOption = Format.TABLE,
) -> None:
    """
    Review apps which use a given addon
    """

    with ThreadPoolExecutor() as executor:
        apps = heroku.apps() if team is None else get_apps_for_teams(team)

        collected_addons = [
            addon
            for addon in get_addons(executor, apps)
            if addon.plan.name.startswith(addon_name)
        ]

    display_data(
        sorted(
            (
                {
                    "App": addon.app.name,
                    "Addon": addon.name,
                    "Plan": get_addon_plan(addon),
                }
                for addon in collected_addons
            ),
            key=operator.itemgetter("App"),
        ),
        display_format,
    )
