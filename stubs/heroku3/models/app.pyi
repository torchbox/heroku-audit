from . import Team
from .addon import Addon
from .collaborator import Collaborator

class App:
    name: str
    team: Team

    def addons(self) -> list[Addon]: ...
    def collaborators(self) -> list[Collaborator]: ...
