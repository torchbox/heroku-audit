from pathlib import Path

from dotenv import load_dotenv
from typer import get_app_dir

APP_DIR = Path(get_app_dir("heroku-audit"))


def load_env_config() -> None:
    env_file = APP_DIR / "config.env"

    if env_file.is_file():
        load_dotenv(env_file)
