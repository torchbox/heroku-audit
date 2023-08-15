from typing import Annotated, Optional
import typer

TeamOption = Annotated[
    Optional[str], typer.Option(help="Limit options to the given team")
]
