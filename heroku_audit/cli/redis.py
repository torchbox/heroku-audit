import operator
from concurrent.futures import ThreadPoolExecutor
from typing import Annotated, Optional, TypedDict

import typer
from heroku3.models.addon import Addon
from rich.progress import track

from heroku_audit.client import heroku
from heroku_audit.format import Format, FormatOption, display_data
from heroku_audit.options import TeamOption
from heroku_audit.utils import SHOW_PROGRESS, get_addon_plan, get_apps_for_teams

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
    Audit the available redis database versions
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
                addon for addon in addons if addon.plan.name.startswith(HEROKU_REDIS)
            )

        results = []
        for addon, addon_details in track(
            executor.map(lambda a: (a, get_heroku_redis_details(a)), collected_addons),
            description="Probing databases...",
            total=len(collected_addons),
            disable=not SHOW_PROGRESS,
        ):
            if target and addon_details["version"].split(".", 1)[0] != str(target):
                continue

            results.append(
                {
                    "App": addon.app.name,
                    "Addon": addon.name,
                    "Plan": get_addon_plan(addon),
                    "Version": addon_details["version"],
                    "Max Memory Policy": addon_details["maxmemory_policy"],
                }
            )

    display_data(sorted(results, key=operator.itemgetter("Version")), display_format)


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
    Find Redis instances with a given plan
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
            key=operator.itemgetter("App"),
        ),
        display_format,
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
    display_format: FormatOption = Format.TABLE,
) -> None:
    """
    Find apps with a given number of instances
    """
    # HACK: https://github.com/martyzz1/heroku3.py/pull/132
    Addon._strs.append("config_vars")  # type: ignore

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
            key=operator.itemgetter("Instances"),
            reverse=True,
        ),
        display_format,
    )


@app.command()
def maxmemory_policy(
    policy: Annotated[
        Optional[str],
        typer.Argument(help="Policy to look for"),
    ] = None,
    team: TeamOption = None,
    display_format: FormatOption = Format.TABLE,
) -> None:
    """
    Audit the redis `maxmemory-policy`
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
                addon for addon in addons if addon.plan.name.startswith(HEROKU_REDIS)
            )

        results = []
        for addon, addon_details in track(
            executor.map(lambda a: (a, get_heroku_redis_details(a)), collected_addons),
            description="Probing databases...",
            total=len(collected_addons),
            disable=not SHOW_PROGRESS,
        ):
            if policy and addon_details["maxmemory_policy"] != policy:
                continue

            results.append(
                {
                    "App": addon.app.name,
                    "Addon": addon.name,
                    "Plan": get_addon_plan(addon),
                    "Policy": addon_details["maxmemory_policy"],
                }
            )

    display_data(sorted(results, key=operator.itemgetter("Policy")), display_format)
