import logging
import re
import threading
import urllib.request

import fasttext

from app.config import HF_HOME

logger = logging.getLogger(__name__)

MODEL_URL = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz"
MODEL_PATH = HF_HOME / "language-detection" / "lid.176.ftz"
MIN_TEXT_LENGTH = 20
MIN_CONFIDENCE = 0.65
WHITESPACE_PATTERN = re.compile(r"\s+")

class LanguageDetector:
    def __init__(self):
        self.model = None
        self.lock = threading.Lock()

    def initialize(self):
        if self.model is not None:
            return

        with self.lock:
            if self.model is not None:
                return

            MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

            if not MODEL_PATH.is_file():
                temp_path = MODEL_PATH.with_suffix(".download")

                try:
                    logger.info("Downloading language detection model")

                    request = urllib.request.Request(
                        MODEL_URL,
                        headers={"User-Agent": "Laya-API/1.0"},
                    )

                    with urllib.request.urlopen(request, timeout=60) as response:
                        with temp_path.open("wb") as output:
                            while chunk := response.read(1024 * 1024):
                                output.write(chunk)

                    if temp_path.stat().st_size == 0:
                        raise RuntimeError("Downloaded language model is empty")

                    temp_path.replace(MODEL_PATH)
                finally:
                    if temp_path.exists():
                        temp_path.unlink()

            self.model = fasttext.load_model(str(MODEL_PATH))
            logger.info("Language detection model is ready")

    def detect(self, text: str) -> dict:
        if self.model is None:
            raise RuntimeError("Language detector is not initialized")

        normalized_text = WHITESPACE_PATTERN.sub(" ", text).strip()

        if len(normalized_text) < MIN_TEXT_LENGTH:
            return {
                "language": "und",
                "confidence": 0.0,
                "fallback": True,
            }

        with self.lock:
            labels, scores = self.model.predict(normalized_text, k=1)

        language = labels[0].replace("__label__", "")
        confidence = float(scores[0])

        return {
            "language": language,
            "confidence": confidence,
            "fallback": confidence < MIN_CONFIDENCE,
        }


language_detector = LanguageDetector()