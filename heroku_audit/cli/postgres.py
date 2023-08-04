import typer
from heroku_audit.client import heroku
from typing import Optional, Annotated, TypedDict
from rich.progress import track
from concurrent.futures import ThreadPoolExecutor
from heroku_audit.format import display_data, FormatOption, Format
from heroku3.models.addon import Addon

app = typer.Typer()

HEROKU_POSTGRES = "heroku-postgresql:"


class HerokuPostgresDetails(TypedDict):
    postgres_version: str


def get_heroku_postgres_details(addon) -> HerokuPostgresDetails:
    if any(x in addon.plan.name for x in ["dev", "basic", "mini"]):
        host = "postgres-starter-api.heroku.com"
    else:
        host = "postgres-api.heroku.com"
    response = heroku._session.get(f"https://{host}/client/v11/databases/{addon.id}")
    response.raise_for_status()
    data = response.json()

    # Reshape for easier parsing
    data["info"] = {i["name"]: i["values"] for i in data["info"]}

    return {"postgres_version": data["info"]["PG Version"][0]}


def get_addon_plan(addon: Addon):
    return addon.plan.name.removeprefix(HEROKU_POSTGRES)


def get_version_column(addon: Addon):
    return {
        "App": addon.app.name,
        "Addon": addon.name,
        "Plan": get_addon_plan(addon),
        "Version": get_heroku_postgres_details(addon)["postgres_version"],
    }


@app.command()
def version(
    target: Annotated[
        Optional[int],
        typer.Argument(help="Version to look for"),
    ] = None,
    format: FormatOption = Format.TABLE,
):
    """
    Audit the available postgres database versions
    """
    with ThreadPoolExecutor() as executor:
        apps = heroku.apps()

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
    format: FormatOption = Format.TABLE,
):
    # HACK: https://github.com/martyzz1/heroku3.py/pull/132
    Addon._strs.append("config_vars")

    with ThreadPoolExecutor() as executor:
        apps = heroku.apps()

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
