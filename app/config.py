
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

HF_HOME = Path(os.getenv("HF_HOME", "./models/cache")).expanduser()
if not HF_HOME.is_absolute():
    HF_HOME = BASE_DIR / HF_HOME
HF_HOME = HF_HOME.resolve()
os.environ["HF_HOME"] = str(HF_HOME)

API_KEY = os.getenv("API_KEY", "").strip()
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_WORKERS = int(os.getenv("API_WORKERS", "1"))

HF_TOKEN = os.getenv("HF_TOKEN", "").strip() or None

LAYA_DEVICE = os.getenv("LAYA_DEVICE", "cuda").strip()
LAYA_PRELOAD = os.getenv("LAYA_PRELOAD", "true").strip().lower() == "true"
LAYA_MAX_LOADED = int(os.getenv("LAYA_MAX_LOADED", "3"))

LAYA_LANGUAGE = list(dict.fromkeys(
    lang.strip().lower()
    for lang in os.getenv("LAYA_LANGUAGE", "en,fa,de").split(",")
    if lang.strip()
))

LAYA_MODELS = {
    "fa": "tarfandoon/laya-fa-support",
}

LAYA_DEFAULT_MODEL = "convaiinnovations/laya-multilingual"

LAYA_SELECTED_MODELS = {}

for lang in LAYA_LANGUAGE:
    if lang == "fa":
        LAYA_SELECTED_MODELS[lang] = LAYA_MODELS["fa"]
    else:
        LAYA_SELECTED_MODELS[lang] = LAYA_DEFAULT_MODEL

LAYA_REQUIRED_MODELS = list(dict.fromkeys(LAYA_SELECTED_MODELS.values()))

API_MAX_REQUEST_LENGTH = int(os.getenv("API_MAX_REQUEST_LENGTH", "12000"))
