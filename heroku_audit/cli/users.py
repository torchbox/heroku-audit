import operator
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import typer
from heroku3.models.collaborator import Collaborator
from rich.progress import track

from heroku_audit.client import heroku
from heroku_audit.format import Format, FormatOption, display_data
from heroku_audit.options import TeamOption
from heroku_audit.style import style_user_role
from heroku_audit.utils import SHOW_PROGRESS, get_apps_for_teams, zip_map

app = typer.Typer(name="users", help="Report on Heroku users.")


def get_member_of_team(team_name: str, email: str) -> Optional[Collaborator]:
    return next(
        (
            collaborator
            for collaborator in heroku._get_resources(  # type:ignore[attr-defined]
                ("teams", team_name, "members"), obj=Collaborator
            )
            if collaborator.user.email == email and collaborator.role != "collaborator"
        ),
        None,
    )


@app.command()
def access(
    account_email: str,
    team: TeamOption = None,
    display_format: FormatOption = Format.TABLE,
) -> None:
    """
    Review apps a user has access to
    """
    # HACK: https://github.com/martyzz1/heroku3.py/pull/133
    Collaborator._strs.append("role")  # type:ignore

    with ThreadPoolExecutor() as executor:
        apps = heroku.apps() if team is None else get_apps_for_teams(team)

        team_membership = {}
        teams = {app.team.name for app in apps}
        for team_name, team_member in track(
            zip_map(executor, lambda t: get_member_of_team(t, account_email), teams),
            description="Loading admin status...",
            total=len(teams),
            disable=not SHOW_PROGRESS,
        ):
            if team_member:
                team_membership[team_name] = team_member

        app_access = {}

        for app, collaborators in track(
            zip_map(executor, lambda a: a.collaborators(), apps),
            description="Loading app collaborators...",
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
            elif app.team.name in team_membership:
                app_access[app] = team_membership[app.team.name]

    display_data(
        sorted(
            (
                {
                    "App": app.name,
                    "Date Given": collaborator.created_at.date().isoformat(),
                    "Role": style_user_role(collaborator.role),
                }
                for app, collaborator in app_access.items()
            ),
            key=operator.itemgetter("App"),
        ),
        display_format,
    )
