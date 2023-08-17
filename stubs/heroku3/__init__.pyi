from requests import Session

from .models.app import App

class Heroku:
    _session: Session

    def apps(self) -> list[App]: ...

def from_key(api_key: str) -> Heroku: ...
