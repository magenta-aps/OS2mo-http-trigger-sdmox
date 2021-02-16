# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0

from os2mo_http_trigger_protocol import (
    EventType,
    MOTriggerPayload,
    MOTriggerRegister,
    RequestType,
)
from pydantic import BaseModel


class DetailError(BaseModel):
    """Default Error model."""

    class Config:
        schema_extra = {
            "example": {
                "detail": "string explaining the error",
            }
        }

    detail: str
