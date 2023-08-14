from rich.table import Table
from rich.console import Console
import csv
from typing import Annotated
from enum import StrEnum
import typer
import json
from io import StringIO


class Format(StrEnum):
    TABLE = "table"
    CSV = "csv"
    JSON = "json"


FormatOption = Annotated[Format, typer.Option()]


def display_data(data: list[dict], format: Format):
    if not data:
        return

    if format == Format.TABLE:
        headers = data[0].keys()
        table = Table(*headers)
        for row in data:
            table.add_row(*[str(c) for c in row.values()])
        Console().print(table)

    elif format == Format.CSV:
        headers = data[0].keys()
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
        output.seek(0)
        print(output.getvalue())

    elif format == Format.JSON:
        print(json.dumps(data))
