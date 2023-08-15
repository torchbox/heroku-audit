from heroku_audit.client import heroku
from heroku3.models.app import App


def get_apps_for_teams(team):
    return heroku._get_resources(("teams", team, "apps"), App)
