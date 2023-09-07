import os
import sys
from typing import Any, cast

import heroku3
from heroku3.core import Heroku
from rich import print
from rich.text import Text

__all__ = ["heroku"]


class LazyHerokuWrapper:
    """
    A lazy heroku wrapper which only requires an API key when it's used
    """

    _heroku = None

    def _get_heroku(self) -> Heroku:
        if self._heroku is None:
            api_key = os.environ.get("HEROKU_API_KEY")
            if api_key is None:
                print(
                    Text(
                        "Please set $HEROKU_API_KEY to a valid Heroku API key.",
                        style="red",
                    )
                )
                sys.exit(1)

            self._heroku = heroku3.from_key(api_key.strip())

        return self._heroku

    def __getattr__(self, attr_name: str) -> Any:
        return getattr(self._get_heroku(), attr_name)


heroku = cast(Heroku, LazyHerokuWrapper())
