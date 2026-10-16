import os
import time
import uuid
from decimal import Decimal, InvalidOperation

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware


EMAIL = os.getenv(
    "EXAM_EMAIL",
    "23f2003924@ds.study.iitm.ac.in",
)

ALLOWED_ORIGIN = "https://dash-a8abo7.example.com"

app = FastAPI()


# Add request ID and process-time headers to every response.
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        request_id = str(uuid.uuid4())

        try:
            response = await call_next(request)
        except Exception:
            response = JSONResponse(
                {"detail": "Internal Server Error"},
                status_code=500,
            )

        elapsed = max(0.0, time.perf_counter() - start_time)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{elapsed:.6f}"

        return response


app.add_middleware(MetricsMiddleware)

# Strict CORS: only the assigned origin is allowed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
    max_age=600,
)


@app.get("/stats")
async def stats(
    values: str = Query(..., description="Comma-separated integers"),
):
    try:
        parts = values.split(",")

        if not parts or any(not part.strip() for part in parts):
            raise ValueError("Empty value")

        numbers = []
        for part in parts:
            number = Decimal(part.strip())

            if not number.is_finite() or number != number.to_integral_value():
                raise ValueError("Values must be integers")

            numbers.append(int(number))

        if not numbers:
            raise ValueError("At least one integer is required")

    except (ValueError, InvalidOperation):
        return JSONResponse(
            {"detail": "values must be comma-separated integers"},
            status_code=400,
        )

    total = sum(numbers)
    count = len(numbers)

    return {
        "email": EMAIL,
        "count": count,
        "sum": total,
        "min": min(numbers),
        "max": max(numbers),
        "mean": total / count,
    }
