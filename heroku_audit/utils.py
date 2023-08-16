from heroku_audit.client import heroku
from heroku3.models.app import App
import sys
from heroku3.models.addon import Addon

SHOW_PROGRESS = sys.stdout.isatty()


def get_apps_for_teams(team):
    return heroku._get_resources(("teams", team, "apps"), App)


def get_addon_plan(addon: Addon):
    return addon.plan.name.split(":", 1)[-1]
