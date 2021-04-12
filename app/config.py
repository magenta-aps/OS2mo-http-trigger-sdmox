# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0

from typing import Dict, List, Optional
from uuid import UUID

from pydantic import AnyHttpUrl, BaseSettings, HttpUrl, PositiveInt
from pydantic.tools import parse_obj_as

from app.pydantic_types import Domain, Port


class Settings(BaseSettings):
    mora_url: AnyHttpUrl = parse_obj_as(AnyHttpUrl, "https://morademo.magenta.dk/")
    saml_token: Optional[UUID] = None

    triggered_uuids: List[UUID]
    ou_levelkeys: List[str]
    ou_time_planning_mo_vs_sd: Dict[str, str]

    amqp_username: str
    amqp_password: str
    amqp_host: Domain = Domain("msg-amqp.silkeborgdata.dk")
    amqp_virtual_host: str
    amqp_port: Port = Port(5672)
    amqp_check_waittime: PositiveInt = PositiveInt(3)
    amqp_check_retries: PositiveInt = PositiveInt(6)

    sd_username: str
    sd_password: str
    sd_institution: str
    sd_base_url: HttpUrl = parse_obj_as(HttpUrl, "https://service.sd.dk/sdws/")

    jaeger_service: str = "SDMox"
    jaeger_hostname: Optional[str] = None
    jaeger_port: Port = Port(6831)


def get_settings(**overrides) -> Settings:
    return Settings(**overrides)
