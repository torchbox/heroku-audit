import os
from pathlib import Path
from typing import Optional

from typer import get_app_dir

APP_DIR = Path(get_app_dir("heroku-audit"))


def config_env_default(
    file_name: str, env_var: str, default: Optional[str] = None
) -> Optional[str]:
    """
    Attempt to load a configuration value.

    Sources, in order:

        1. Environment variable named `env_var`
        2. Config file in app dir with name `file_name`
        3. `default`
    """
    if env_value := os.environ.get(env_var):
        return env_value

    config_file = APP_DIR / file_name
    if config_file.is_file():
        return config_file.read_text()

    return default
