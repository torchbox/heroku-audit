import csv
import json
from enum import Enum
from io import StringIO
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.protocol import is_renderable
from rich.table import Table


class RichJSONEncoder(json.JSONEncoder):
    """
    A custom JSON encoder which handles `rich` datatypes
    """

    def default(self, o: Any) -> Any:
        if is_renderable(o):
            return str(o)

        return super().default(o)


class Format(str, Enum):
    TABLE = "table"
    CSV = "csv"
    JSON = "json"


FormatOption = Annotated[Format, typer.Option("--format")]


def display_data(data: list[dict], display_format: Format) -> None:
    if not data:
        return

    if display_format == Format.TABLE:
        headers = data[0].keys()
        table = Table(*headers)
        for row in data:
            values = [v if is_renderable(v) else str(v) for v in row.values()]
            table.add_row(*values)
        Console().print(table)

    elif display_format == Format.CSV:
        headers = data[0].keys()
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
        output.seek(0)
        print(output.getvalue())

    elif display_format == Format.JSON:
        print(json.dumps(data, cls=RichJSONEncoder))
