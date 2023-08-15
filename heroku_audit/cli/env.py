import typer
from heroku_audit.client import heroku
from typing import Optional, Annotated
from rich.progress import track
from concurrent.futures import ThreadPoolExecutor
from heroku_audit.format import display_data, FormatOption, Format
from heroku_audit.utils import get_apps_for_teams
from rich.text import Text
from collections import defaultdict
import fnmatch
import re

app = typer.Typer()


@app.command()
def value_of(
    key: Annotated[str, typer.Argument(help="Variable to audit")],
    unset_only: Annotated[
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

            if value is not None and unset_only:
                continue

            app_values[app] = value if value is not None else Text("UNSET", style="red")

    display_data(
        sorted(
            ({"App": app.name, "Value": value} for app, value in app_values.items()),
            key=lambda r: r["App"],
        ),
        format,
    )


@app.command()
def contains(
    target: Annotated[
        str, typer.Argument(help="Value to search for. Glob syntax is supported.")
    ],
    team: Annotated[
        Optional[str], typer.Option(help="Limit options to the given team")
    ] = None,
    format: FormatOption = Format.TABLE,
):
    """
    Find applications with a given environment variable value set.
    """

    target_matcher = re.compile(fnmatch.translate(target))
    with ThreadPoolExecutor() as executor:
        apps = heroku.apps() if team is None else get_apps_for_teams(team)

        matches = defaultdict(list)

        for app, config_vars in track(
            executor.map(lambda a: (a, a.config()), apps),
            description="Loading config...",
            total=len(apps),
        ):
            for key, val in config_vars.to_dict().items():
                if target_matcher.match(val):
                    matches[app].append(key)

    display_data(
        sorted(
            (
                {
                    "App": app.name,
                    "Match Count": len(matched_variables),
                    "Matches": ", ".join(sorted(matched_variables)),
                }
                for app, matched_variables in matches.items()
            ),
            key=lambda r: (r["Match Count"], r["App"]),
        ),
        format,
    )
