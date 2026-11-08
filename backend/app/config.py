"""Configuración leída desde variables de entorno (.env). Nunca hardcodear secretos."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "InvoiceChaser"
    environment: str = "development"  # development | production
    demo_mode: bool = True  # habilita el simulador de pagos y el usuario demo
    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173"  # lista separada por comas, nunca "*"

    # Base de datos
    database_url: str = "sqlite:///./invoicechaser.db"

    # Auth
    jwt_secret: str = "cambia-esto-en-produccion-con-un-secreto-largo"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 12

    # Correo (Resend). Sin API key los correos se imprimen en consola.
    resend_api_key: str = ""
    email_from: str = "InvoiceChaser <onboarding@resend.dev>"

    # Pagos (Wompi). Usar llaves de sandbox (pub_test_..., test_integrity_..., test_events_...).
    wompi_public_key: str = ""
    wompi_integrity_secret: str = ""
    wompi_events_secret: str = ""
    wompi_checkout_url: str = "https://checkout.wompi.co/p/"

    # Recordatorios
    timezone: str = "America/Bogota"
    # Días respecto al vencimiento: negativo = antes, 0 = el día, positivo = vencida.
    reminder_offsets: str = "-3,0,7,14,21"
    # Mínimo de días entre recordatorios de cobro de facturas vencidas (inspirado en la Ley 2300 de 2023).
    min_days_between_overdue: int = 7

    # Versión vigente de la política de datos (Ley 1581). Se guarda con cada aceptación.
    privacy_policy_version: str = "2026-11-08"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip() and o.strip() != "*"]

    @property
    def reminder_offset_list(self) -> list[int]:
        return sorted(int(x) for x in self.reminder_offsets.split(",") if x.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
