import fnmatch
import operator
from concurrent.futures import ThreadPoolExecutor
from typing import Annotated

import typer
from rich.progress import track

from heroku_audit.client import heroku
from heroku_audit.format import Format, FormatOption, display_data
from heroku_audit.options import TeamOption
from heroku_audit.utils import SHOW_PROGRESS, get_apps_for_teams

app = typer.Typer(name="domains", help="Report on domains.")


@app.command()
def matches(
    pattern: Annotated[str, typer.Argument(help="Domain glob to search for")],
    team: TeamOption = None,
    display_format: FormatOption = Format.TABLE,
) -> None:
    """
    Find the value of a given environment variable
    """
    with ThreadPoolExecutor() as executor:
        apps = heroku.apps() if team is None else get_apps_for_teams(team)

        domain_matches = []

        for domains in track(
            executor.map(lambda a: a.domains(), apps),
            description="Loading domains...",
            total=len(apps),
            disable=not SHOW_PROGRESS,
        ):
            for domain in domains:
                if fnmatch.fnmatch(domain.hostname, pattern):
                    domain_matches.append(domain)

    display_data(
        sorted(
            (
                {
                    "App": domain.app.name,
                    "Domain": domain.hostname,
                    "CNAME": domain.cname,
                }
                for domain in domain_matches
            ),
            key=operator.itemgetter("App"),
        ),
        display_format,
    )
