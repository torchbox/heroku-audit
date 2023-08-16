import typer
from heroku_audit.options import TeamOption
from heroku_audit.utils import get_apps_for_teams, SHOW_PROGRESS, get_addon_plan
from heroku_audit.format import FormatOption, display_data, Format
from concurrent.futures import ThreadPoolExecutor
from heroku_audit.client import heroku
from typing import Annotated, Optional, TypedDict
from heroku3.models.addon import Addon
from rich.progress import track


app = typer.Typer(name="redis", help="Report on Heroku Data for Redis.")

HEROKU_REDIS = "heroku-redis:"


class HerokuRedisDetails(TypedDict):
    version: str
    maxmemory_policy: str


def get_heroku_redis_details(addon: Addon) -> dict:
    response = heroku._session.get(
        f"https://redis-api.heroku.com/redis/v0/databases/{addon.id}"
    )
    response.raise_for_status()
    data = response.json()

    # Reshape for easier parsing
    data["info"] = {i["name"]: i["values"] for i in data["info"]}

    return {
        "version": data["info"]["Version"][0],
        "maxmemory_policy": data["info"]["Maxmemory"][0],
    }


def get_version_column(addon: Addon):
    details = get_heroku_redis_details(addon)
    return {
        "App": addon.app.name,
        "Addon": addon.name,
        "Plan": get_addon_plan(addon),
        "Version": details["version"],
        "Max Memory Policy": details["maxmemory_policy"],
    }


def get_maxmemory_policy_column(addon: Addon):
    details = get_heroku_redis_details(addon)
    return {
        "App": addon.app.name,
        "Addon": addon.name,
        "Plan": get_addon_plan(addon),
        "Policy": details["maxmemory_policy"],
    }


@app.command()
def major_version(
    target: Annotated[
        Optional[int],
        typer.Option(help="Version to look for"),
    ] = None,
    team: TeamOption = None,
    format: FormatOption = Format.TABLE,
):
    """
    Audit the available redis database versions
    """
    with ThreadPoolExecutor() as executor:
        apps = heroku.apps() if team is None else get_apps_for_teams(team)

        collected_addons = []
        for addons in track(
            executor.map(lambda a: a.addons(), apps),
            description="Loading addons...",
            total=len(apps),
            disable=not SHOW_PROGRESS,
        ):
            collected_addons.extend(
                addon for addon in addons if addon.plan.name.startswith(HEROKU_REDIS)
            )

        results = []
        for result in track(
            executor.map(get_version_column, collected_addons),
            description="Probing databases...",
            total=len(collected_addons),
            disable=not SHOW_PROGRESS,
        ):
            if target and result["Version"].split(".", 1)[0] != str(target):
                continue
            results.append(result)

    display_data(sorted(results, key=lambda r: r["Version"]), format)


@app.command()
def plan(
    plan: Annotated[
        Optional[str],
        typer.Argument(help="Plan to look for"),
    ] = None,
    team: TeamOption = None,
    format: FormatOption = Format.TABLE,
):
    """
    Find Redis instances with a given plan
    """
    # HACK: https://github.com/martyzz1/heroku3.py/pull/132
    Addon._strs.append("config_vars")

    with ThreadPoolExecutor() as executor:
        apps = heroku.apps() if team is None else get_apps_for_teams(team)

        collected_addons = []
        for addons in track(
            executor.map(lambda a: a.addons(), apps),
            description="Loading addons...",
            total=len(apps),
            disable=not SHOW_PROGRESS,
        ):
            collected_addons.extend(
                addon for addon in addons if addon.plan.name.startswith(HEROKU_REDIS)
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
        format,
    )


@app.command()
def count(
    minimum: Annotated[
        int,
        typer.Option(
            "--min",
            help="Acceptable number of instances (greater than this will be shown)",
        ),
    ] = 1,
    team: TeamOption = None,
    format: FormatOption = Format.TABLE,
):
    """
    Find apps with a given number of instances
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
            disable=not SHOW_PROGRESS,
        ):
            app_to_addons[app] = [
                addon for addon in addons if addon.plan.name.startswith(HEROKU_REDIS)
            ]

    display_data(
        sorted(
            (
                {
                    "App": app.name,
                    "Instances": len(addons),
                    "Addon Names": ", ".join(sorted([a.name for a in addons])),
                }
                for app, addons in app_to_addons.items()
                if len(addons) >= minimum
            ),
            key=lambda r: r["Instances"],
            reverse=True,
        ),
        format,
    )


@app.command()
def maxmemory_policy(
    policy: Annotated[
        Optional[str],
        typer.Argument(help="Policy to look for"),
    ] = None,
    team: TeamOption = None,
    format: FormatOption = Format.TABLE,
):
    """
    Audit the redis `maxmemory-policy`
    """
    with ThreadPoolExecutor() as executor:
        apps = heroku.apps() if team is None else get_apps_for_teams(team)

        collected_addons = []
        for addons in track(
            executor.map(lambda a: a.addons(), apps),
            description="Loading addons...",
            total=len(apps),
            disable=not SHOW_PROGRESS,
        ):
            collected_addons.extend(
                addon for addon in addons if addon.plan.name.startswith(HEROKU_REDIS)
            )

        results = []
        for result in track(
            executor.map(get_maxmemory_policy_column, collected_addons),
            description="Probing databases...",
            total=len(collected_addons),
            disable=not SHOW_PROGRESS,
        ):
            if policy and result["Policy"] != policy:
                continue
            results.append(result)

    display_data(sorted(results, key=lambda r: r["Policy"]), format)
