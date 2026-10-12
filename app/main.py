
import asyncio
import hmac
import logging
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

from fastapi import Depends, FastAPI, Header, HTTPException, status

from app.config import API_KEY, LAYA_DEFAULT_MODEL
from app.model_manager import model_manager
from app.schemas import PredictRequest, PredictResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    initialization = loop.run_in_executor(
        executor,
        model_manager.initialize,
    )

    app.state.model_initialization = initialization

    try:
        await initialization
    except Exception:
        logger.exception("Application initialization failed")

    yield

    executor.shutdown(wait=False, cancel_futures=True)


app = FastAPI(
    title="Laya API",
    description="Multilingual AI inference API with automatic language detection",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

async def require_api_key(
    x_api_key: str = Header(default="", alias="X-API-Key"),
):
    if not API_KEY or not hmac.compare_digest(x_api_key, API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


@app.get("/health")
async def health():
    return {
        "status": model_manager.status,
        "ready": model_manager.ready,
        "error": model_manager.error,
    }


@app.get("/v1/models", dependencies=[Depends(require_api_key)])
async def models():
    return {
        "models": list(model_manager.registered_models.keys()),
        "default_model": (
            LAYA_DEFAULT_MODEL
            if LAYA_DEFAULT_MODEL in model_manager.registered_models
            else None
        ),
    }


@app.post(
    "/v1/predict",
    response_model=PredictResponse,
    dependencies=[Depends(require_api_key)],
)
async def predict(request: PredictRequest):
    if not model_manager.ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": "Models are not ready",
                "status": model_manager.status,
            },
            headers={"Retry-After": "10"},
        )

    try:
        result = await asyncio.to_thread(
            model_manager.predict,
            request.state,
            request.questions,
        )
        return PredictResponse(result=result)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
            headers={"Retry-After": "10"},
        ) from exc
