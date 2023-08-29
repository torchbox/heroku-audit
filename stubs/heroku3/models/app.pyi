from . import Team
from .addon import Addon

class App:
    name: str
    team: Team

    def addons(self) -> list[Addon]: ...
