import typer
from . import postgres, env

app = typer.Typer(help="Heroku audit tool")

app.add_typer(postgres.app, name="postgres")
app.add_typer(env.app, name="env")
