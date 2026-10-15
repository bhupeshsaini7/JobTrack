"""Reads settings from the .env file so passwords are never written in the code."""
import os

from dotenv import load_dotenv

load_dotenv()  # loads the values from the .env file into the environment


def get_required_setting(name):
    """Return a setting from .env, or stop with a clear message if it is missing."""
    value = os.getenv(name)
    if value is None or value == "":
        raise RuntimeError(
            f"Missing setting: {name}. "
            "Copy .env.example to .env and fill in your values."
        )
    return value


class Config:
    # Required: the app will not start without these
    SECRET_KEY = get_required_setting("SECRET_KEY")
    DB_USER = get_required_setting("DB_USER")
    DB_PASSWORD = get_required_setting("DB_PASSWORD")

    # Optional: these have sensible defaults
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_NAME = os.getenv("DB_NAME", "jobtrack")