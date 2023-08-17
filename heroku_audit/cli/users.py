import operator
from concurrent.futures import ThreadPoolExecutor

import typer
from rich.progress import track

from heroku_audit.client import heroku
from heroku_audit.format import Format, FormatOption, display_data
from heroku_audit.options import TeamOption
from heroku_audit.utils import SHOW_PROGRESS, get_apps_for_teams, zip_map

app = typer.Typer(name="users", help="Report on Heroku users.")


@app.command()
def access(
    account_email: str,
    team: TeamOption = None,
    display_format: FormatOption = Format.TABLE,
) -> None:
    """
    Review apps a user has access to
    """
    with ThreadPoolExecutor() as executor:
        apps = heroku.apps() if team is None else get_apps_for_teams(team)

        app_access = {}

        for app, collaborators in track(
            zip_map(executor, lambda a: a.collaborators(), apps),
            description="Loading formation...",
            total=len(apps),
            disable=not SHOW_PROGRESS,
        ):
            target_collaborator = next(
                (
                    collaborator
                    for collaborator in collaborators
                    if collaborator.user.email == account_email
                ),
                None,
            )

            if target_collaborator:
                app_access[app] = target_collaborator

    display_data(
        sorted(
            (
                {
                    "App": app.name,
                    "Date Given": collaborator.created_at.date().isoformat(),
                }
                for app, collaborator in app_access.items()
            ),
            key=operator.itemgetter("App"),
        ),
        display_format,
    )
