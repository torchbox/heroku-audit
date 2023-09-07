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

    def __get__(self, obj: Any, objtype: Any = None) -> Heroku:
        if self._heroku is None:
            try:
                self._heroku = heroku3.from_key(os.environ["HEROKU_API_KEY"])
            except KeyError:
                print(
                    Text(
                        "Please set $HEROKU_API_KEY to a valid Heroku API key.",
                        style="red",
                    )
                )
                sys.exit(1)
        return self._heroku


heroku = cast(Heroku, LazyHerokuWrapper())
