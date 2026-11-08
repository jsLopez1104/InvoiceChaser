import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlmodel import Session

from .config import get_settings
from .db import engine, init_db
from .limiter import limiter
from .routers import auth, clients, dashboard, invoices, reminders, webhooks
from .seed import seed_demo
from .services.reminders import process_reminders

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
settings = get_settings()

if settings.environment == "production" and settings.jwt_secret == "cambia-esto-en-produccion-con-un-secreto-largo":
    raise RuntimeError("Define JWT_SECRET en producción")


def reminder_job() -> None:
    with Session(engine) as session:
        process_reminders(session)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.demo_mode:
        with Session(engine) as session:
            seed_demo(session)
    scheduler = None
    if settings.environment != "test":
        scheduler = BackgroundScheduler(timezone=settings.timezone)
        scheduler.add_job(reminder_job, "cron", minute=0, id="reminders")  # cada hora en punto
        scheduler.start()
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(title="InvoiceChaser API", version="1.0.0", lifespan=lifespan,
              description="Persigue facturas sin pagar para que tú no tengas que hacerlo.")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: lista blanca explícita, nunca "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if not request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


for r in (auth, clients, invoices, dashboard, reminders, webhooks):
    app.include_router(r.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "demo_mode": settings.demo_mode}
