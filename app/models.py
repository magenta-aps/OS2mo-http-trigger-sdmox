# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0

from os2mo_http_trigger_protocol import (EventType, MOTriggerPayload,
                                         MOTriggerRegister, RequestType)
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


class MOTriggerPayloadOUCreate(MOTriggerPayload):
    class Config:
        schema_extra = {
            "example": {
                "event_type": "ON_BEFORE",
                "request": {
                    "validity": {"from": "2021-02-19", "to": None},
                    "name": "Ny enhed",
                    "parent": None,
                    "org_unit_level": {
                        "name": "N1",
                        "scope": "TEXT",
                        "user_key": "N1",
                        "uuid": "84f95e29-48a0-4175-85fd-84a1f596e1a4",
                    },
                    "org_unit_type": {
                        "name": "Direkt\u00f8romr\u00e5de",
                        "scope": "TEXT",
                        "user_key": "Direkt\u00f8romr\u00e5de",
                        "uuid": "51203743-f2db-4f17-a7e1-fee48c178799",
                    },
                    "details": [],
                },
                "request_type": "CREATE",
                "role_type": "org_unit",
                "uuid": "389edd41-eb7f-468e-a02e-de4312f28bb3",
            }
        }


class MOTriggerPayloadOUEdit(MOTriggerPayload):
    class Config:
        schema_extra = {
            "example": {
                "event_type": "ON_BEFORE",
                "request": {
                    "type": "org_unit",
                    "data": {
                        "name": "Social og sundhed",
                        "uuid": "25abf6f4-fa38-5bd8-b217-7130ce3552cd",
                        "clamp": True,
                        "validity": {"from": "2021-02-19"},
                    },
                },
                "request_type": "EDIT",
                "role_type": "org_unit",
                "uuid": "25abf6f4-fa38-5bd8-b217-7130ce3552cd",
            }
        }


class MOTriggerPayloadAddressCreate(MOTriggerPayload):
    class Config:
        schema_extra = {
            "example": {
                "event_type": "ON_BEFORE",
                "request": {
                    "address_type": {
                        "name": "Postadresse",
                        "scope": "DAR",
                        "user_key": "AddressMailUnit",
                        "uuid": "5260d4aa-e33b-48f7-ae3e-6074262cbdcf",
                    },
                    "org": {
                        "name": "Kolding Kommune",
                        "user_key": "Kolding Kommune",
                        "uuid": "3b866d97-0b1f-48e0-8078-686d96f430b3",
                    },
                    "org_unit": {"uuid": "25abf6f4-fa38-5bd8-b217-7130ce3552cd"},
                    "value": "0a3f5090-524d-32b8-e044-0003ba298018",
                    "validity": {"from": "2021-02-19", "to": None},
                    "type": "address",
                },
                "request_type": "CREATE",
                "role_type": "address",
                "uuid": "ea85d638-c233-4558-9bd4-8f15a7b37d5b",
            }
        }


class MOTriggerPayloadAddressEdit(MOTriggerPayload):
    class Config:
        schema_extra = {
            "example": {
                "event_type": "ON_BEFORE",
                "request": {
                    "data": {
                        "address_type": {
                            "name": "Postadresse",
                            "scope": "DAR",
                            "user_key": "AddressMailUnit",
                            "uuid": "5260d4aa-e33b-48f7-ae3e-6074262cbdcf",
                        },
                        "href": "https://www.openstreetmap.org/?mlon=9.48789506&mlat=55.47580072&zoom=16",
                        "name": "Sct. Knuds Vej 2, 6000 Kolding",
                        "org_unit": {
                            "name": "Social og sundhed",
                            "user_key": "Social og sundhed",
                            "uuid": "25abf6f4-fa38-5bd8-b217-7130ce3552cd",
                            "validity": {"from": "1960-01-01", "to": None},
                        },
                        "user_key": "0a3f50bc-0796-32b8-e044-0003ba298018",
                        "uuid": "94897da9-377c-4386-b073-303e25dd6894",
                        "validity": {"from": "2021-02-01", "to": None},
                        "value": "0a3f5090-6e66-32b8-e044-0003ba298018",
                        "type": "address",
                        "address": {"value": "0a3f5090-52af-32b8-e044-0003ba298018"},
                        "org": {
                            "name": "Kolding Kommune",
                            "user_key": "Kolding Kommune",
                            "uuid": "3b866d97-0b1f-48e0-8078-686d96f430b3",
                        },
                    },
                    "org_unit": {"uuid": "25abf6f4-fa38-5bd8-b217-7130ce3552cd"},
                    "type": "address",
                    "uuid": "94897da9-377c-4386-b073-303e25dd6894",
                },
                "request_type": "EDIT",
                "role_type": "address",
                "uuid": "94897da9-377c-4386-b073-303e25dd6894",
            }
        }
