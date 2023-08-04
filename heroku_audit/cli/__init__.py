import typer
from . import postgres

app = typer.Typer(help="Heroku audit tool")

app.add_typer(postgres.app, name="postgres")
