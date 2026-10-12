
import logging
import threading
from typing import Any

from laya import Router

from app.config import (
    HF_TOKEN,
    LAYA_DEVICE,
    LAYA_MAX_LOADED,
    LAYA_PRELOAD,
    LAYA_REQUIRED_MODELS,
    LAYA_DEFAULT_MODEL,
    LAYA_MODELS,
)
from app.language_detector import language_detector

logger = logging.getLogger(__name__)


class ModelManager:
    def __init__(self):
        self.registered_models = {}
        self.router = None
        self.status = "starting"
        self.error = None
        self.lock = threading.RLock()

    @property
    def ready(self) -> bool:
        return self.status == "ready" and self.router is not None

    def initialize(self):
        with self.lock:
            self.status = "starting"
            self.error = None

        try:
            if not LAYA_REQUIRED_MODELS:
                raise RuntimeError("No languages are configured in LAYA_LANGUAGE")

            language_detector.initialize()

            router = Router(
                device=LAYA_DEVICE,
                token=HF_TOKEN,
                max_loaded=LAYA_MAX_LOADED,
            )

            registered_models = {}

            for index, model_id in enumerate(LAYA_REQUIRED_MODELS):
                model_name = f"model_{index}"
                router.register(model_name, model_id)
                registered_models[model_id] = model_name

            if LAYA_PRELOAD:
                router.preload(list(registered_models.values()))

            with self.lock:
                self.router = router
                self.registered_models = registered_models
                self.status = "ready"

            logger.info(
                "Laya models are ready: %s",
                list(registered_models.keys()),
            )

        except Exception as exc:
            logger.exception("Failed to initialize Laya models")

            with self.lock:
                self.router = None
                self.registered_models = {}
                self.status = "error"
                self.error = str(exc)

            raise

    def predict(
        self,
        state: Any,
        questions: dict[str, dict[str, Any]],
    ):
        with self.lock:
            if not self.ready:
                raise RuntimeError("Service is not ready")

            router = self.router
            registered_models = self.registered_models

        detection = language_detector.detect(str(state))
        language = detection["language"]

        if detection["fallback"]:
            if LAYA_DEFAULT_MODEL in registered_models:
                model_id = LAYA_DEFAULT_MODEL
            elif len(registered_models) == 1:
                model_id = next(iter(registered_models))
            else:
                raise RuntimeError("No fallback model is configured")
        elif language == "fa":
            model_id = LAYA_MODELS["fa"]
            if model_id not in registered_models:
                if LAYA_DEFAULT_MODEL in registered_models:
                    model_id = LAYA_DEFAULT_MODEL
                elif len(registered_models) == 1:
                    model_id = next(iter(registered_models))
                else:
                    raise RuntimeError("No model is configured for Persian")
        else:
            if LAYA_DEFAULT_MODEL in registered_models:
                model_id = LAYA_DEFAULT_MODEL
            elif len(registered_models) == 1:
                model_id = next(iter(registered_models))
            else:
                raise RuntimeError(
                    f"No model is configured for language: {language}"
                )

        model_name = registered_models[model_id]

        logger.info(
            "Selected model: %s; detected language: %s; confidence: %.3f",
            model_id,
            language,
            detection["confidence"],
        )

        return router.predict(
            state,
            questions,
            model=model_name,
        )


model_manager = ModelManager()
