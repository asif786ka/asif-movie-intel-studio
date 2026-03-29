from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def setup_opentelemetry(app):
    if not settings.otel_enabled:
        logger.info("OpenTelemetry disabled")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        resource = Resource.create({"service.name": settings.otel_service_name})
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(app)
        logger.info(f"OpenTelemetry enabled for service: {settings.otel_service_name}")
    except ImportError as e:
        logger.warning(f"OpenTelemetry dependencies not available: {e}")
    except Exception as e:
        logger.error(f"OpenTelemetry setup failed: {e}")
