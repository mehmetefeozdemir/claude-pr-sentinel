from typing import Optional
import hashlib
import hmac
import json
import logging
import logging.config
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from config import config
from reviewer import handle_pull_request_event

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "format": '{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","message":"%(message)s"}'
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
            }
        },
        "root": {"level": "INFO", "handlers": ["console"]},
    }
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("claude-pr-sentinel starting on port %d", config.PORT)
    yield
    logger.info("claude-pr-sentinel shutting down")


app = FastAPI(title="claude-pr-sentinel", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _verify_signature(body: bytes, signature_header: Optional[str]) -> bool:
    """Verify the GitHub webhook HMAC-SHA256 signature.

    Args:
        body: Raw request body bytes.
        signature_header: Value of the X-Hub-Signature-256 header.

    Returns:
        True if the signature is valid, False otherwise.
    """
    if not signature_header:
        return False

    expected_sig = (
        "sha256="
        + hmac.new(
            config.GITHUB_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
    )
    return hmac.compare_digest(expected_sig, signature_header)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> JSONResponse:
    """Liveness check."""
    return JSONResponse({"status": "ok"})


@app.post("/webhook")
async def webhook(request: Request) -> JSONResponse:
    """Receive and process GitHub webhook events.

    Args:
        request: The incoming HTTP request.

    Returns:
        A JSON response indicating the processing result.
    """
    body = await request.body()

    # Verify signature
    signature = request.headers.get("X-Hub-Signature-256")
    if not _verify_signature(body, signature):
        logger.warning("Webhook signature verification failed")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    # Parse event type
    event_type = request.headers.get("X-GitHub-Event", "")
    logger.info("Received GitHub event: %s", event_type)

    if event_type == "ping":
        return JSONResponse({"message": "pong"})

    if event_type != "pull_request":
        return JSONResponse({"message": f"Event '{event_type}' ignored"})

    # Parse payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse webhook payload: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON") from exc

    # Process asynchronously (fire-and-forget is fine for webhook ack)
    try:
        await handle_pull_request_event(payload)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error handling pull_request event: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Review failed",
        ) from exc

    return JSONResponse({"message": "Review posted"})
