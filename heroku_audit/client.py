import os
import heroku3
from rich.text import Text
from rich import print

try:
    heroku = heroku3.from_key(os.environ["HEROKU_API_KEY"])
except KeyError:
    print(Text("Please set $HEROKU_API_KEY to a valid Heroku API key.", style="red"))
    exit(1)
