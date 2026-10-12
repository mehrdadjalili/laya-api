# Laya API

A multilingual AI inference API built with FastAPI and Laya, featuring automatic language detection, intelligent model routing, API key authentication, health monitoring, interactive API documentation, and Docker support.

## Features

- Automatic language detection from input text.
- Dedicated Persian support model.
- Multilingual fallback for other languages and uncertain predictions.
- Configurable API key authentication.
- Health endpoint for monitoring service readiness.
- Interactive Swagger UI and ReDoc documentation.
- Model caching to reduce repeated downloads.
- CPU inference support and optional CUDA acceleration, subject to model compatibility.
- Docker-based deployment.

## Models

| Purpose | Model |
|---|---|
| Persian inference | `tarfandoon/laya-fa-support` |
| Default multilingual inference | `convaiinnovations/laya-multilingual` |
| Language detection | FastText `lid.176.ftz` |

The API detects the language from the `state` field and selects the appropriate inference model.

- Persian (`fa`): Uses the Persian support model when detection confidence is sufficient.
- Other languages: Uses the multilingual model.
- Short text or low-confidence detection: Falls back to the multilingual model.

Clients do not need to provide a language parameter.

## Requirements

- Python 3.12 recommended
- pip
- Docker (optional)
- A compatible NVIDIA GPU and CUDA-enabled dependencies (optional)

## Project Structure

```text
laya-api/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── language_detector.py
│   ├── main.py
│   ├── model_manager.py
│   └── schemas.py
├── models/
├── .env
├── .env.example
├── .dockerignore
├── .gitignore
├── Dockerfile
├── requirements.txt
└── README.md
```

## Installation

Clone the repository:

```bash
git clone git@github.com:mehrdadjalili/laya-api.git
cd laya-api
```

### Windows PowerShell

Create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Python 3.12 is recommended because native dependencies such as FastText may not install successfully on newer Python versions or every platform.

## Configuration

Create a `.env` file in the project root:

```env
API_KEY=replace-with-a-long-random-secret
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
HF_HOME=./models/cache
HF_TOKEN=
LAYA_DEVICE=cpu
LAYA_PRELOAD=true
LAYA_MAX_LOADED=2
API_MAX_REQUEST_LENGTH=12000
```

### Environment Variables

| Variable | Description |
|---|---|
| `API_KEY` | Secret key required for protected endpoints |
| `API_HOST` | Host interface for the API server |
| `API_PORT` | Port used by the API server |
| `API_WORKERS` | Configured number of server workers |
| `HF_HOME` | Cache directory for downloaded models |
| `HF_TOKEN` | Optional Hugging Face access token |
| `LAYA_DEVICE` | Inference device, such as `cpu` or `cuda` |
| `LAYA_PRELOAD` | Whether to preload inference models during startup |
| `LAYA_MAX_LOADED` | Maximum number of models retained by the model router |
| `API_MAX_REQUEST_LENGTH` | Maximum configured request length |

Use `LAYA_DEVICE=cpu` for CPU inference.

Use `LAYA_DEVICE=cuda` only when the installed Laya and PyTorch dependencies support CUDA and a compatible GPU is available.

Do not commit your `.env` file or expose your API key in public repositories.

## Running Locally

Start the API server:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The server may download and initialize models during startup. The first startup can take longer depending on your network, available memory, and model size.

## API Documentation

FastAPI provides interactive API documentation.

| Documentation | URL |
|---|---|
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| OpenAPI JSON | `http://localhost:8000/openapi.json` |

### Using Swagger UI

1. Start the API server.
2. Open `http://localhost:8000/docs`.
3. Expand an endpoint.
4. Click **Try it out**.
5. Enter the required request body and headers.
6. Click **Execute** to send the request and inspect the response.

### Swagger Authentication

Protected endpoints require an API key in the `X-API-Key` header.

```http
X-API-Key: your-api-key
```

If authentication is implemented using a custom FastAPI dependency, Swagger may not display a global **Authorize** button. To enable that button, define the API key using FastAPI's `APIKeyHeader` security scheme and use that security dependency on protected endpoints.

## API Endpoints

| Method | Endpoint | Authentication | Description |
|---|---|---|---|
| `GET` | `/health` | Not required | Reports service readiness |
| `GET` | `/v1/models` | Required | Lists registered inference models |
| `POST` | `/v1/predict` | Required | Runs inference using automatic language detection |
| `GET` | `/docs` | Not required by default | Swagger UI |
| `GET` | `/redoc` | Not required by default | ReDoc documentation |
| `GET` | `/openapi.json` | Not required by default | OpenAPI specification |

Documentation endpoints are public by default unless the application or deployment configuration restricts them.

## Health Check

Check whether the service is ready:

```http
GET /health
```

Example response when ready:

```json
{
  "status": "ready",
  "ready": true,
  "error": null
}
```

The service may report these states:

- `starting`: Model or language detector initialization is in progress.
- `ready`: The service is initialized and can process predictions.
- `error`: Initialization failed.

The endpoint is intended for monitoring and health checks.

## List Models

Request:

```http
GET /v1/models
X-API-Key: your-api-key
```

The response lists the models registered with the model router and the default multilingual model.

## Run a Prediction

Endpoint:

```http
POST /v1/predict
Content-Type: application/json
X-API-Key: your-api-key
```

Example request:

```json
{
  "state": "سلام، دو بار پول از حسابم کم شده ولی اشتراکم فعال نشده",
  "questions": {
    "department": {
      "type": "choice",
      "instructions": "Which department should handle this support request?",
      "criteria": {
        "billing": "Payment issues, charges, and refunds",
        "technical": "Bugs and technical problems",
        "cancel": "Subscription cancellation",
        "other": "Other requests"
      }
    },
    "urgency": {
      "type": "score",
      "instructions": "How urgent is this issue?",
      "criteria": [
        "Low",
        "Normal",
        "High",
        "Critical"
      ]
    },
    "churn_risk": {
      "type": "noul",
      "instructions": "Has the customer threatened to cancel their subscription?"
    }
  }
}
```

### Request Fields

| Field | Type | Description |
|---|---|---|
| `state` | String, object, or array | Input state used for language detection and inference |
| `questions` | Object | Questions and criteria passed to the selected model |

The exact question types and supported criteria depend on the installed Laya version and the selected model.

### Language Detection and Routing

The API uses the text in `state` to detect the language.

1. The language detector analyzes the input text.
2. If Persian is detected with sufficient confidence, the Persian support model is selected.
3. Otherwise, the multilingual model is selected.
4. Short text and low-confidence detections use the multilingual fallback.

The client does not need to send a separate language field.

### Prediction Response

The response follows the `PredictResponse` schema defined by the application. It contains a `result` field with the inference output.

Example response structure:

```json
{
  "result": {}
}
```

The actual contents of `result` depend on the model output and the requested questions.

## Error Handling

| HTTP Status | Meaning |
|---|---|
| `200 OK` | Request completed successfully |
| `401 Unauthorized` | API key is missing or invalid |
| `422 Unprocessable Entity` | Request body validation failed |
| `503 Service Unavailable` | Models or language detector are not ready |

When the service is not ready, the prediction endpoint returns `503 Service Unavailable`. Clients can retry after a short delay.

## Docker Deployment

### Build the Image

```bash
docker build -t laya-api:latest .
```

### Run the Container

```bash
docker run -d --name laya-api -p 8000:8000 --env-file .env -v laya-model-cache:/app/models/cache laya-api:latest
```

The named Docker volume preserves cached model files between container runs.

### View Logs

```bash
docker logs -f laya-api
```

### Stop the Container

```bash
docker stop laya-api
```

### Remove the Container

```bash
docker rm laya-api
```

After startup, open:

- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## Production Considerations

- Use a strong, randomly generated API key.
- Keep secrets out of version control.
- Use HTTPS when exposing the API publicly.
- Restrict public access to documentation endpoints if required.
- Monitor the health endpoint and application logs.
- Persist the model cache using a Docker volume.
- Ensure the available RAM and GPU memory are sufficient for the configured models.
- Verify that the installed Laya version supports the router methods used by the application.
- Test model initialization and prediction before publishing a production image.
- Confirm that worker and model-loading settings are compatible with the available hardware.

## License

Add a `LICENSE` file specifying the license under which this project is distributed.

Review the licenses and usage terms of the Laya models and the FastText language identification model separately before redistributing them.
