import json
from dataclasses import dataclass, asdict
from pathlib import Path

SETTINGS_DIR = Path.home() / ".legosupersoftware"
SETTINGS_PATH = SETTINGS_DIR / "settings.json"


@dataclass
class AppSettings:
    competition: str = "WRO"
    ai_mode: str = "auto"  # auto | openai | local | local_multi
    openai_model: str = "gpt-5"
    openai_api_key: str = ""
    remember_api_key: bool = False
    image_detail: str = "auto"  # auto | low | high
    include_images: bool = True
    local_model_path: str = ""
    local_code_model_path: str = ""
    local_tutorial_model_path: str = ""
    local_image_model_path: str = ""
    temperature: float = 0.2
    max_output_tokens: int = 1400


def load_settings() -> AppSettings:
    if not SETTINGS_PATH.exists():
        return AppSettings()

    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return AppSettings()

    settings = AppSettings()
    for key, value in data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)

    if not settings.remember_api_key:
        settings.openai_api_key = ""

    return settings


def save_settings(settings: AppSettings) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    data = asdict(settings)

    if not settings.remember_api_key:
        data["openai_api_key"] = ""

    SETTINGS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
