import sys
from concurrent.futures import Executor
from typing import Callable, Iterable

from heroku3.models.addon import Addon
from heroku3.models.app import App
from heroku3.models.collaborator import Collaborator
from rich.progress import track

from heroku_audit.client import heroku

SHOW_PROGRESS = sys.stdout.isatty()
COLLABORATOR_ROLES = {"collaborator", None}


def get_apps_for_teams(team: str) -> list[App]:
    return heroku._get_resources(  # type:ignore[attr-defined,no-any-return]
        ("teams", team, "apps"), App
    )


def get_team_members(team: str) -> list[Collaborator]:
    return [
        member
        for member in heroku._get_resources(  # type:ignore[attr-defined]
            ("teams", team, "members"), obj=Collaborator
        )
        if member.role not in COLLABORATOR_ROLES
    ]


def get_addon_plan(addon: Addon) -> str:
    return addon.plan.name.split(":", 1)[-1]


def zip_map(executor: Executor, fn: Callable, iterable: Iterable) -> Iterable:
    """
    Concurrently maps `list[T]` to `list[(T, fn(T))]`
    """
    yield from executor.map(lambda a: (a, fn(a)), iterable)


def get_addons(executor: Executor, apps: list[App]) -> Iterable[Addon]:
    for app_addons in track(
        executor.map(App.addons, apps),
        description="Fetching addons...",
        total=len(apps),
        disable=not SHOW_PROGRESS,
    ):
        yield from app_addons
