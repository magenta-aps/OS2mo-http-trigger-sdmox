# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from datetime import date
from functools import partial
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Query, status
from os2mo_helpers.mora_helpers import MoraHelper
from requests.exceptions import ConnectionError

from app.config import get_settings
from app.models import DetailError
from app.sd_mox import SDMox, SDMoxInterface
from app.util import first_of_month


def should_mox_run(mo_ou: dict):
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


async def _ou_edit_name(ou_uuid: UUID, new_name: str, at: date, dry_run: bool):
    assert new_name is not None, "_ou_edit_name called without new_name"

    print("Changing name")
    mox: SDMoxInterface = SDMox(from_date=at)
    await mox.rename_unit(ou_uuid, new_name, at=at, dry_run=dry_run)


async def _ou_edit_parent(ou_uuid: UUID, new_parent: UUID, at: date, dry_run: bool):
    assert new_parent is not None, "_ou_edit_name called without new_parent"

    print("Changing parent")
    mox: SDMoxInterface = SDMox(from_date=at)
    await mox.move_unit(ou_uuid, new_parent, at=at, dry_run=dry_run)


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
    except ConnectionError:
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


_verify_ou_ok_responses = {
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
