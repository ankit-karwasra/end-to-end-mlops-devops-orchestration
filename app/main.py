"""FastAPI application entry point."""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

#sgg

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.logging_config import configure_logging
from app.model_loader import load_current_model
from app.predictor import predict_price
from app.schema import HealthResponse, ModelInfoResponse, PredictionRequest, PredictionResponse

logger = logging.getLogger("house_price_api")
BASE_DIR = Path(__file__).resolve().parents[1]
INDEX_TEMPLATE = (BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    model, entry = load_current_model()
    app.state.model = model
    app.state.model_entry = entry
    logger.info(
        "Application startup complete",
        extra={
            "event": "startup",
            "model_version": entry["version"] if entry else None,
        },
    )
    yield


app = FastAPI(
    title="House Price Prediction API",
    version="1.0.0",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    entry = app.state.model_entry
    sample_input = {
        "MedInc": 8.3252,
        "HouseAge": 41.0,
        "AveRooms": 6.984127,
        "AveBedrms": 1.02381,
        "Population": 322.0,
        "AveOccup": 2.555556,
        "Latitude": 37.88,
        "Longitude": -122.23,
    }
    metrics = entry["metrics"] if entry else {}
    replacements = {
        "__APP_NAME__": "House Price Prediction System",
        "__TAGLINE__": "Production-style MLOps demo with live predictions, model metadata, and deployment-friendly APIs.",
        "__MODEL_VERSION__": entry["version"] if entry else "Unavailable",
        "__DATA_SOURCE__": entry["data_source"] if entry else "Unavailable",
        "__RMSE__": f"{metrics.get('rmse', 0):.4f}" if metrics else "N/A",
        "__MAE__": f"{metrics.get('mae', 0):.4f}" if metrics else "N/A",
        "__R2__": f"{metrics.get('r2', 0):.4f}" if metrics else "N/A",
        "__SAMPLE_INPUT_JSON__": json.dumps(sample_input),
        "__STATIC_STYLE__": str(request.url_for("static", path="style.css")),
        "__STATIC_APP__": str(request.url_for("static", path="app.js")),
    }
    html = INDEX_TEMPLATE
    for key, value in replacements.items():
        html = html.replace(key, value)
    return HTMLResponse(content=html)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    entry = app.state.model_entry
    return HealthResponse(
        status="ok",
        model_loaded=app.state.model is not None,
        model_version=entry["version"] if entry else None,
    )


@app.get("/model/info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    entry = app.state.model_entry
    if entry is None:
        return ModelInfoResponse(current_version=None, metrics=None, data_source=None)
    return ModelInfoResponse(
        current_version=entry["version"],
        metrics=entry["metrics"],
        data_source=entry["data_source"],
    )


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest) -> PredictionResponse:
    if app.state.model is None or app.state.model_entry is None:
        raise HTTPException(status_code=503, detail="No model is currently available")
    prediction = predict_price(app.state.model, payload)
    version = app.state.model_entry["version"]
    logger.info(
        "Prediction generated",
        extra={"event": "prediction", "model_version": version},
    )
    return PredictionResponse(prediction=prediction, model_version=version)
