import sys

from heroku3.models.addon import Addon
from heroku3.models.app import App

from heroku_audit.client import heroku

SHOW_PROGRESS = sys.stdout.isatty()


def get_apps_for_teams(team: str) -> list[App]:
    return heroku._get_resources(  # type:ignore[attr-defined,no-any-return]
        ("teams", team, "apps"), App
    )


def get_addon_plan(addon: Addon) -> str:
    return addon.plan.name.split(":", 1)[-1]
