from pydantic import BaseModel

from os2mo_http_trigger_protocol import (
    EventType,
    MOTriggerPayload,
    MOTriggerRegister,
    RequestType,
)

class DetailError(BaseModel):
    """Default Error model."""

    class Config:
        schema_extra = {
            "example": {
                "detail": "string explaining the error",
            }
        }

    detail: str
