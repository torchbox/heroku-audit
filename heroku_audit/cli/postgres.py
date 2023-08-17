from concurrent.futures import ThreadPoolExecutor
from typing import Annotated, Optional, TypedDict

import typer
from heroku3.models.addon import Addon
from rich.progress import track
from rich.text import Text

from heroku_audit.client import heroku
from heroku_audit.format import Format, FormatOption, display_data
from heroku_audit.options import TeamOption
from heroku_audit.utils import SHOW_PROGRESS, get_addon_plan, get_apps_for_teams

app = typer.Typer(name="postgres", help="Report on Heroku Postgres databases.")

HEROKU_POSTGRES = "heroku-postgresql:"


def get_postgres_api_hostname(addon: Addon) -> str:
    if any(x in addon.plan.name for x in ["dev", "basic", "mini"]):
        return "postgres-starter-api.heroku.com"
    return "postgres-api.heroku.com"


class HerokuPostgresDetails(TypedDict):
    postgres_version: str


def get_heroku_postgres_details(addon: Addon) -> HerokuPostgresDetails:
    host = get_postgres_api_hostname(addon)
    response = heroku._session.get(f"https://{host}/client/v11/databases/{addon.id}")
    response.raise_for_status()
    data = response.json()

    # Reshape for easier parsing
    data["info"] = {i["name"]: i["values"] for i in data["info"]}

    return {"postgres_version": data["info"]["PG Version"][0]}


def get_heroku_postgres_backup_schedules(addon: Addon) -> list[str]:
    host = get_postgres_api_hostname(addon)
    response = heroku._session.get(
        f"https://{host}/client/v11/databases/{addon.id}/transfer-schedules"
    )
    response.raise_for_status()
    data = response.json()

    return [f"Daily at {s['hour']}:00 {s['timezone']}" for s in data]


@app.command()
def major_version(
    target: Annotated[
        Optional[int],
        typer.Option(help="Version to look for"),
    ] = None,
    team: TeamOption = None,
    display_format: FormatOption = Format.TABLE,
) -> None:
    """
    Audit the available postgres database versions
    """
    with ThreadPoolExecutor() as executor:
        apps = heroku.apps() if team is None else get_apps_for_teams(team)

        collected_addons: list[Addon] = []
        for addons in track(
            executor.map(lambda a: a.addons(), apps),
            description="Loading addons...",
            total=len(apps),
            disable=not SHOW_PROGRESS,
        ):
            collected_addons.extend(
                addon for addon in addons if addon.plan.name.startswith(HEROKU_POSTGRES)
            )

        results = []
        for addon, addon_details in track(
            executor.map(
                lambda a: (a, get_heroku_postgres_details(a)), collected_addons
            ),
            description="Probing databases...",
            total=len(collected_addons),
            disable=not SHOW_PROGRESS,
        ):
            if target and addon_details["postgres_version"].split(".", 1)[0] != str(
                target
            ):
                continue
            results.append(
                {
                    "App": addon.app.name,
                    "Addon": addon.name,
                    "Plan": get_addon_plan(addon),
                    "Version": addon_details["postgres_version"],
                }
            )

    display_data(sorted(results, key=lambda r: r["Version"]), display_format)


@app.command()
def plan(
    plan: Annotated[
        Optional[str],
        typer.Argument(help="Plan to look for"),
    ] = None,
    team: TeamOption = None,
    display_format: FormatOption = Format.TABLE,
) -> None:
    """
    Find Heroku Postgres instances with a given plan
    """
    # HACK: https://github.com/martyzz1/heroku3.py/pull/132
    Addon._strs.append("config_vars")  # type:ignore

    with ThreadPoolExecutor() as executor:
        apps = heroku.apps() if team is None else get_apps_for_teams(team)

        collected_addons: list[Addon] = []
        for addons in track(
            executor.map(lambda a: a.addons(), apps),
            description="Loading addons...",
            total=len(apps),
            disable=not SHOW_PROGRESS,
        ):
            collected_addons.extend(
                addon for addon in addons if addon.plan.name.startswith(HEROKU_POSTGRES)
            )

    if plan:
        collected_addons = [
            addon for addon in collected_addons if get_addon_plan(addon) == plan
        ]

    display_data(
        sorted(
            (
                {
                    "App": addon.app.name,
                    "Addon": addon.name,
                    "Attachments": ", ".join(sorted(addon.config_vars)),
                    "Plan": get_addon_plan(addon),
                }
                for addon in collected_addons
            ),
            key=lambda r: r["App"],
        ),
        display_format,
    )


@app.command()
def count(
    minimum: Annotated[
        int,
        typer.Option(
            "--min",
            help="Acceptable number of databases (greater than this will be shown)",
        ),
    ] = 1,
    team: TeamOption = None,
    display_format: FormatOption = Format.TABLE,
) -> None:
    """
    Find apps with a given number of databases
    """
    # HACK: https://github.com/martyzz1/heroku3.py/pull/132
    Addon._strs.append("config_vars")  # type:ignore

    with ThreadPoolExecutor() as executor:
        apps = heroku.apps() if team is None else get_apps_for_teams(team)

        app_to_addons = {}

        for app, addons in track(
            executor.map(lambda a: (a, a.addons()), apps),
            description="Loading addons...",
            total=len(apps),
            disable=not SHOW_PROGRESS,
        ):
            app_to_addons[app] = [
                addon for addon in addons if addon.plan.name.startswith(HEROKU_POSTGRES)
            ]

    display_data(
        sorted(
            (
                {
                    "App": app.name,
                    "Databases": len(addons),
                    "Addon Names": ", ".join(sorted([a.name for a in addons])),
                }
                for app, addons in app_to_addons.items()
                if len(addons) >= minimum
            ),
            key=lambda r: r["Databases"],
            reverse=True,
        ),
        display_format,
    )


@app.command()
def backup_schedule(
    team: TeamOption = None,
    missing_only: Annotated[
        Optional[bool],
        typer.Option(help="Only show databases without backup schedules"),
    ] = False,
    display_format: FormatOption = Format.TABLE,
) -> None:
    """
    Find backup schedules for databases
    """

    with ThreadPoolExecutor() as executor:
        apps = heroku.apps() if team is None else get_apps_for_teams(team)

        collected_addons: list[Addon] = []
        for addons in track(
            executor.map(lambda a: a.addons(), apps),
            description="Loading addons...",
            total=len(apps),
            disable=not SHOW_PROGRESS,
        ):
            collected_addons.extend(
                addon for addon in addons if addon.plan.name.startswith(HEROKU_POSTGRES)
            )

        results = []
        for addon, backup_schedules in track(
            executor.map(
                lambda a: (a, get_heroku_postgres_backup_schedules(a)), collected_addons
            ),
            description="Probing databases...",
            total=len(collected_addons),
            disable=not SHOW_PROGRESS,
        ):
            if missing_only and backup_schedules:
                continue

            results.append(
                {
                    "App": addon.app.name,
                    "Addon": addon.name,
                    "Plan": get_addon_plan(addon),
                    "Schedule": ", ".join(backup_schedules)
                    if backup_schedules
                    else Text("NONE", style="red"),
                }
            )

    display_data(sorted(results, key=lambda r: r["App"]), display_format)
