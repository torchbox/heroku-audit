from .app import App
from .plan import Plan

class Addon:
    id: str  # noqa:A003
    plan: Plan
    name: str
    app: App

    # HACK: https://github.com/martyzz1/heroku3.py/pull/132
    config_vars: list[str]
