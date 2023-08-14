import typer
from heroku_audit.client import heroku
from typing import Optional, Annotated, TypedDict
from rich.progress import track
from concurrent.futures import ThreadPoolExecutor
from heroku_audit.format import display_data, FormatOption, Format
from heroku3.models.addon import Addon
from heroku3.models.app import App

app = typer.Typer()

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


def get_heroku_postgres_backup_schedules(addon: Addon) -> HerokuPostgresDetails:
    host = get_postgres_api_hostname(addon)
    response = heroku._session.get(
        f"https://{host}/client/v11/databases/{addon.id}/transfer-schedules"
    )
    response.raise_for_status()
    data = response.json()

    return [f"Daily at {s['hour']}:00 {s['timezone']}" for s in data]


def get_addon_plan(addon: Addon):
    return addon.plan.name.removeprefix(HEROKU_POSTGRES)


def get_apps_for_teams(team):
    return heroku._get_resources(("teams", team, "apps"), App)


def get_version_column(addon: Addon):
    return {
        "App": addon.app.name,
        "Addon": addon.name,
        "Plan": get_addon_plan(addon),
        "Version": get_heroku_postgres_details(addon)["postgres_version"],
    }


def get_backup_column(addon: Addon):
    return {
        "App": addon.app.name,
        "Addon": addon.name,
        "Plan": get_addon_plan(addon),
        "Schedule": ", ".join(get_heroku_postgres_backup_schedules(addon)),
    }


@app.command()
def version(
    target: Annotated[
        Optional[int],
        typer.Argument(help="Version to look for"),
    ] = None,
    team: Annotated[
        Optional[str], typer.Option(help="Limit options to the given team")
    ] = None,
    format: FormatOption = Format.TABLE,
):
    """
    Audit the available postgres database versions
    """
    with ThreadPoolExecutor() as executor:
        apps = heroku.apps() if team is None else get_apps_for_teams(team)

        collected_addons = []
        for addons in track(
            executor.map(lambda a: a.addons(), apps),
            description="Loading addons...",
            total=len(apps),
        ):
            collected_addons.extend(
                addon for addon in addons if addon.plan.name.startswith(HEROKU_POSTGRES)
            )

        results = []
        for result in track(
            executor.map(get_version_column, collected_addons),
            description="Probing databases...",
            total=len(collected_addons),
        ):
            if target and result["Version"].split(".", 1)[0] != str(target):
                continue
            results.append(result)

    display_data(sorted(results, key=lambda r: r["Version"]), format)


@app.command()
def plan(
    target: Annotated[
        Optional[str],
        typer.Argument(help="Plan to look for"),
    ] = None,
    team: Annotated[
        Optional[str], typer.Option(help="Limit options to the given team")
    ] = None,
    format: FormatOption = Format.TABLE,
):
    # HACK: https://github.com/martyzz1/heroku3.py/pull/132
    Addon._strs.append("config_vars")

    with ThreadPoolExecutor() as executor:
        apps = heroku.apps() if team is None else get_apps_for_teams(team)

        collected_addons = []
        for addons in track(
            executor.map(lambda a: a.addons(), apps),
            description="Loading addons...",
            total=len(apps),
        ):
            collected_addons.extend(
                addon for addon in addons if addon.plan.name.startswith(HEROKU_POSTGRES)
            )

    if target:
        collected_addons = [
            addon for addon in collected_addons if get_addon_plan(addon) == target
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
        format,
    )


@app.command()
def count(
    count: Annotated[
        int,
        typer.Argument(
            help="Acceptable number of addons (greater than this will be shown)"
        ),
    ] = 0,
    team: Annotated[
        Optional[str], typer.Option(help="Limit options to the given team")
    ] = None,
    format: FormatOption = Format.TABLE,
):
    """
    Find addons with a given number of databases
    """
    # HACK: https://github.com/martyzz1/heroku3.py/pull/132
    Addon._strs.append("config_vars")

    with ThreadPoolExecutor() as executor:
        apps = heroku.apps() if team is None else get_apps_for_teams(team)

        app_to_addons = {}

        for app, addons in track(
            executor.map(lambda a: (a, a.addons()), apps),
            description="Loading addons...",
            total=len(apps),
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
                if len(addons) >= count
            ),
            key=lambda r: r["Databases"],
            reverse=True,
        ),
        format,
    )


@app.command()
def backup_schedule(
    team: Annotated[
        Optional[str], typer.Option(help="Limit options to the given team")
    ] = None,
    missing: Annotated[
        Optional[bool],
        typer.Option(help="Only show databases without backup schedules"),
    ] = False,
    format: FormatOption = Format.TABLE,
):
    """
    Find backup schedules for databases
    """

    with ThreadPoolExecutor() as executor:
        apps = heroku.apps() if team is None else get_apps_for_teams(team)

        collected_addons = []
        for addons in track(
            executor.map(lambda a: a.addons(), apps),
            description="Loading addons...",
            total=len(apps),
        ):
            collected_addons.extend(
                addon for addon in addons if addon.plan.name.startswith(HEROKU_POSTGRES)
            )

        results = []
        for result in track(
            executor.map(get_backup_column, collected_addons),
            description="Probing databases...",
            total=len(collected_addons),
        ):
            if missing and result["Schedule"]:
                continue
            results.append(result)

    display_data(sorted(results, key=lambda r: r["App"]), format)
