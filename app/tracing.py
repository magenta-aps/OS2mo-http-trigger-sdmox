# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0

import structlog
from fastapi import Request
from opentelemetry import trace
from opentelemetry.exporter import jaeger
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
from structlog import get_logger
from structlog.contextvars import (
    bind_contextvars,
    clear_contextvars,
    merge_contextvars,
    unbind_contextvars,
)

from app.config import Settings, get_settings


def setup_instrumentation(app):
    settings: Settings = get_settings()

    _TRACE_PROVIDER = TracerProvider()
    trace.set_tracer_provider(_TRACE_PROVIDER)

    if settings.jaeger_hostname:
        _JAEGER_EXPORTER = jaeger.JaegerSpanExporter(
            service_name=settings.jaeger_service,
            agent_host_name=settings.jaeger_hostname,
            agent_port=settings.jaeger_port,
        )

        _TRACE_PROVIDER.add_span_processor(BatchExportSpanProcessor(_JAEGER_EXPORTER))

    AioHttpClientInstrumentor().instrument()
    RequestsInstrumentor().instrument()

    # Register logging middleware
    app.middleware("http")(log_requests_middleware)
    app.middleware("http")(bind_logger_tracecontext_middleware)

    FastAPIInstrumentor.instrument_app(app)
    return app


async def bind_logger_tracecontext_middleware(request: Request, call_next):
    spancontext = trace.get_current_span().get_span_context()

    clear_contextvars()
    bind_contextvars(
        trace_id=hex(spancontext.trace_id),
        span_id=hex(spancontext.span_id),
    )
    response = await call_next(request)
    unbind_contextvars("trace_id", "span_id")

    response.headers["X-Trace-ID"] = hex(spancontext.trace_id)
    response.headers["X-Span-ID"] = hex(spancontext.span_id)

    return response


async def log_requests_middleware(request: Request, call_next):
    logger = get_logger()
    logger.debug(
        "Request received",
        method=request.method,
        url=request.url.path,
        query_parameters=str(request.query_params),
        client=request.client,
    )

    response = await call_next(request)
    return response


def setup_logging():
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.TimeStamper(),
            merge_contextvars,
            structlog.processors.KeyValueRenderer(
                key_order=["event", "trace_id", "span_id"]
            ),
        ]
    )
