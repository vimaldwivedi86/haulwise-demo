import pathlib

import yaml

CONFIG_DIR = pathlib.Path(__file__).parent / "config"


def load_processors() -> list[dict]:
    f = CONFIG_DIR / "processors.yaml"
    if not f.exists():
        return []
    data = yaml.safe_load(f.read_text()) or {}
    return data.get("processors", [])


def load_retention() -> list[dict]:
    f = CONFIG_DIR / "retention.yaml"
    if not f.exists():
        return []
    data = yaml.safe_load(f.read_text()) or {}
    return data.get("retained_on_withdrawal", [])
