# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
#
# Triggerkoden i dette modul har to funktioner:
# 1) At oprette/rette/flytte en afdeling i SD, inden det sker i OS2mo.
# 2) At forhinde oprettelse/flytning/rettelse i OS2mo, hvis det ikke lykkedes i SD.
#
# Adressernes rækkefølge har betydning.
#
# Der skal findes en postadresse inden man opretter et PNummer,
# ellers går tilbagemeldingen fra SD tilsyneladende i ged.
# - Der er indført et check for det i sd_mox.py

import sys

sys.path.insert(0, "/")

from datetime import date, datetime
from functools import partial
from typing import Dict, List, Optional
from uuid import UUID

import requests
from fastapi import Depends, FastAPI, HTTPException, Path, Query, status
from fastapi.responses import RedirectResponse
from os2mo_helpers.mora_helpers import MoraHelper

from app.config import get_settings
from app.models import *
from app.sd_mox import SDMox, SDMoxInterface
from app.util import first_of_month, get_mora_helper

tags_metadata = [
    {
        "name": "Meta",
        "description": "Various meta endpoints",
    },
    {
        "name": "API",
        "description": "Direct API for end-users.",
    },
    {
        "name": "Trigger API",
        "description": "Trigger API for mo-triggers.",
        "externalDocs": {
            "description": "OS2MO Trigger docs",
            "url": "https://os2mo.readthedocs.io/en/development/api/triggers.html",
        },
    },
]
app = FastAPI(
    title="SDMox",
    description="API to make changes in SD.",
    version="0.0.1",
    openapi_tags=tags_metadata,
)
# Called for side-effect
get_settings()


def should_mox_run(mo_ou):
    """Determine whether sdmox should trigger code for this organizational unit.

    This is determined by whether the UUID of the unit is in the
    triggered_uuids settings variable.
    """
    # TODO: Consider a parent iterator
    while mo_ou and mo_ou["uuid"]:
        if UUID(mo_ou["uuid"]) in get_settings().triggered_uuids:
            return True
        mo_ou = mo_ou["parent"]
    return False


def get_date(
    date: Optional[date] = Query(
        None,
        description=(
            "Effective start date for change."
            + "<br/>"
            + "Must be the first day of a month."
            + "<br/>"
            "If omitted it will default to the first of the current month."
        ),
    )
):
    if date:
        return date
    return first_of_month()


def _verify_ou_ok(uuid: UUID, at: date, mora_helper: MoraHelper):
    try:
        # TODO: AIOHTTP MoraHelpers?
        mo_ou = mora_helper.read_ou(uuid, at=at)
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not establish a connection to MO",
        )

    if "error_key" in mo_ou and mo_ou["error_key"] == "E_ORG_UNIT_NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested organizational unit was not found in MO",
        )

    if not should_mox_run(mo_ou):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The requested organizational unit is outside the configured allow list",
        )


_verify_ou_ok.responses = {
    status.HTTP_502_BAD_GATEWAY: {
        "model": DetailError,
        "description": (
            "Bad Gateway Error"
            + "<br/><br/>"
            + "Returned when unable to establish a connection to MO."
        ),
    },
    status.HTTP_404_NOT_FOUND: {
        "model": DetailError,
        "description": (
            "Not Found Error"
            + "<br/><br/>"
            + "Returned when the requested organizational unit cannot be found in MO."
        ),
    },
    status.HTTP_403_FORBIDDEN: {
        "model": DetailError,
        "description": (
            "Forbidden Error"
            + "<br/><br/>"
            + "Returned when the requested organizational unit is outside the configured allow list."
        ),
    },
}


def verify_ou_ok(
    uuid: UUID,
    at: date = Depends(get_date),
    mora_helper: MoraHelper = Depends(partial(get_mora_helper, None)),
):
    _verify_ou_ok(uuid, at, mora_helper)


verify_ou_ok.responses = _verify_ou_ok.responses


def verify_ou_ok_trigger(
    payload: MOTriggerPayload,
    mora_helper: MoraHelper = Depends(partial(get_mora_helper, None)),
):
    uuid = payload.uuid
    data = payload.request["data"]

    at = data["validity"]["from"]
    _verify_ou_ok(uuid, at, mora_helper)


verify_ou_ok_trigger.responses = _verify_ou_ok.responses


async def _ou_edit_name(ou_uuid: UUID, new_name: str, at: date, dry_run: bool):
    assert new_name is not None, "_ou_edit_name called without new_name"

    print("Changing name")
    mox: SDMoxInterface = SDMox(from_date=at)
    await mox.rename_unit(str(ou_uuid), new_name, at=at, dry_run=dry_run)


async def _ou_edit_parent(ou_uuid: UUID, new_parent: UUID, at: date, dry_run: bool):
    assert new_parent is not None, "_ou_edit_name called without new_parent"

    print("Changing parent")
    mox: SDMoxInterface = SDMox(from_date=at)
    await mox.move_unit(str(ou_uuid), new_parent, at=at, dry_run=dry_run)


@app.get(
    "/", response_class=RedirectResponse, tags=["Meta"], summary="Redirect to /docs"
)
async def root() -> RedirectResponse:
    """Redirect to /docs."""
    return RedirectResponse(url="/docs")


@app.patch(
    "/ou/{uuid}/edit/name",
    responses=verify_ou_ok.responses,
    dependencies=[Depends(verify_ou_ok)],
    tags=["API"],
    summary="Rename an organizational unit.",
)
async def ou_edit_name(
    uuid: UUID = Path(..., description="UUID of the organizational unit to rename."),
    new_name: str = Query(..., description="The name we wish to change to."),
    dry_run: Optional[bool] = Query(False, description="Dry run the operation."),
    at: date = Depends(get_date),
):
    """Rename an organizational unit."""
    await _ou_edit_name(uuid, new_name, at, dry_run=dry_run)
    return {"status": "OK"}


@app.patch(
    "/ou/{uuid}/edit/parent",
    responses=verify_ou_ok.responses,
    dependencies=[Depends(verify_ou_ok)],
    tags=["API"],
    summary="Move an organizational unit.",
)
async def ou_edit_parent(
    uuid: UUID = Path(..., description="UUID of the organizational unit to move."),
    new_parent: UUID = Query(..., description="The parent unit we wish to move under."),
    dry_run: Optional[bool] = Query(False, description="Dry run the operation."),
    at: date = Depends(get_date),
):
    """Move an organizational unit."""
    await _ou_edit_parent(uuid, new_parent, at, dry_run=dry_run)
    return {"status": "OK"}


@app.get(
    "/triggers",
    tags=["Trigger API"],
    summary="List triggers to be registered.",
    response_model=List[MOTriggerRegister],
    response_description=(
        "Successful Response" + "<br/>" + "List of triggers to register."
    ),
)
def triggers() -> List[MOTriggerRegister]:
    """List triggers to be registered."""
    # All our triggers are ON_BEFORE
    triggers = [
        (RequestType.CREATE, "org_unit", triggers_ou_create),
        (RequestType.EDIT, "org_unit", triggers_ou_edit),
        (RequestType.CREATE, "address", triggers_address_create),
        (RequestType.EDIT, "address", triggers_address_edit),
    ]
    return [
        MOTriggerRegister(
            event_type=EventType.ON_BEFORE,
            request_type=request_type,
            role_type=role_type,
            url=app.url_path_for(method.__name__),
        )
        for request_type, role_type, method in triggers
    ]


@app.post(
    "/triggers/ou/create",
    tags=["Trigger API"],
    summary="Create an organizational unit.",
)
async def triggers_ou_create(
    payload: MOTriggerPayloadOUCreate,
    dry_run: Optional[bool] = Query(False, description="Dry run the operation."),
    mora_helper=Depends(partial(get_mora_helper, None)),
):
    """Create an organizational unit."""
    print("/triggers/ou/create called")
    print(payload.json(indent=4))

    # We will never create a top level organization unit with SDMox.
    # Thus we cannot accept requests with no parent set, or the parent set to the
    # root organization.
    parent_uuid = payload.request.get("parent", {}).get("uuid")
    o_uuid = mora_helper.read_organisation()
    if not parent_uuid or parent_uuid == o_uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create an organizational unit at top-level.",
        )

    # We will never create an organization under a non-triggered uuid.
    at = datetime.strptime(payload.request["validity"]["from"], "%Y-%m-%d").date()
    _verify_ou_ok(parent_uuid, at, mora_helper)

    # Preconditions have been checked, time to try to create the organizational unit
    uuid = str(payload.uuid)
    unit_data = payload.request
    parent_data = mora_helper.read_ou(parent_uuid, at=at)
    mox: SDMoxInterface = SDMox(from_date=at)
    await mox.create_unit(uuid, unit_data, parent_data, dry_run=dry_run)

    return {"status": "OK"}


@app.post(
    "/triggers/ou/edit",
    responses=verify_ou_ok_trigger.responses,
    dependencies=[Depends(verify_ou_ok_trigger)],
    tags=["Trigger API"],
    summary="Rename or move an organizational unit.",
)
async def triggers_ou_edit(
    payload: MOTriggerPayloadOUEdit,
    dry_run: Optional[bool] = Query(False, description="Dry run the operation."),
):
    """Rename or move an organizational unit."""
    print("/triggers/ou/edit called")
    print(payload.json(indent=4))

    uuid = str(payload.uuid)
    data = payload.request["data"]

    at = datetime.strptime(data["validity"]["from"], "%Y-%m-%d").date()

    if "name" in data:
        new_name = data["name"]
        await _ou_edit_name(uuid, new_name, at, dry_run=dry_run)

    if "parent" in data:
        new_parent_obj = data["parent"]
        new_parent_uuid = new_parent_obj["uuid"]
        await _ou_edit_parent(uuid, new_parent_uuid, at, dry_run=dry_run)
    return {"status": "OK"}


@app.post(
    "/triggers/address/create",
    tags=["Trigger API"],
    summary="Create an addresses.",
)
async def triggers_address_create(
    payload: MOTriggerPayloadAddressCreate,
    dry_run: Optional[bool] = Query(False, description="Dry run the operation."),
    mora_helper=Depends(partial(get_mora_helper, None)),
):
    """Create an addresses."""
    print("/triggers/address/create called")
    print(payload.json(indent=4))

    unit_uuid = payload.request.get("org_unit", {}).get("uuid")
    if not unit_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing organization unit UUID when adding address.",
        )
    # We will never create an addresses for units outside non-triggered uuid.
    # TODO: Consider whether we should block inserts in these cases, probably not
    at = datetime.strptime(payload.request["validity"]["from"], "%Y-%m-%d").date()
    _verify_ou_ok(unit_uuid, at, mora_helper)

    # Preconditions have been checked, time to try to create the organizational unit
    address_uuid = str(payload.uuid)
    address_data = payload.request
    mox: SDMoxInterface = SDMox(from_date=at)
    await mox.create_address(unit_uuid, address_uuid, address_data, at, dry_run=dry_run)

    return {"status": "OK"}


@app.post(
    "/triggers/address/edit",
    tags=["Trigger API"],
    summary="Edit an address.",
)
async def triggers_address_edit(
    payload: MOTriggerPayloadAddressEdit,
    dry_run: Optional[bool] = Query(False, description="Dry run the operation."),
    mora_helper=Depends(partial(get_mora_helper, None)),
):
    """Edit an address."""
    print("/triggers/address/edit called")
    print(payload.json(indent=4))

    unit_uuid = payload.request.get("org_unit", {}).get("uuid")
    if not unit_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing organization unit UUID when adding address.",
        )
    # We will never create an addresses for units outside non-triggered uuid.
    # TODO: Consider whether we should block inserts in these cases, probably not
    at = datetime.strptime(
        payload.request["data"]["validity"]["from"], "%Y-%m-%d"
    ).date()
    _verify_ou_ok(unit_uuid, at, mora_helper)

    # Preconditions have been checked, time to try to create the organizational unit
    address_uuid = str(payload.uuid)
    address_data = payload.request["data"]
    mox: SDMoxInterface = SDMox(from_date=at)
    await mox.create_address(unit_uuid, address_uuid, address_data, at, dry_run=dry_run)

    return {"status": "OK"}
