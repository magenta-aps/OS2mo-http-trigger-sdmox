# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, Path, Query
from os2mo_helpers.mora_helpers import MoraHelper

from app.dependencies import (_ou_edit_name, _ou_edit_parent, _verify_ou_ok,
                              _verify_ou_ok_responses, get_date)
from app.util import first_of_month, get_mora_helper_default

router = APIRouter()


def verify_ou_ok(
    uuid: UUID,
    at: date = Depends(get_date),
    mora_helper: MoraHelper = Depends(get_mora_helper_default),
):
    _verify_ou_ok(uuid, at, mora_helper)


@router.patch(
    "/ou/{uuid}/edit/name",
    responses=_verify_ou_ok_responses,
    dependencies=[Depends(verify_ou_ok)],
    summary="Rename an organizational unit.",
)
async def ou_edit_name(
    uuid: UUID = Path(..., description="UUID of the organizational unit to rename."),
    new_name: str = Query(..., description="The name we wish to change to."),
    dry_run: Optional[bool] = Query(False, description="Dry run the operation."),
    at: date = Depends(get_date),
):
    """Rename an organizational unit."""
    dry_run = dry_run or False
    await _ou_edit_name(uuid, new_name, at, dry_run=dry_run)
    return {"status": "OK"}


@router.patch(
    "/ou/{uuid}/edit/parent",
    responses=_verify_ou_ok_responses,
    dependencies=[Depends(verify_ou_ok)],
    summary="Move an organizational unit.",
)
async def ou_edit_parent(
    uuid: UUID = Path(..., description="UUID of the organizational unit to move."),
    new_parent: UUID = Query(..., description="The parent unit we wish to move under."),
    dry_run: Optional[bool] = Query(False, description="Dry run the operation."),
    at: date = Depends(get_date),
):
    """Move an organizational unit."""
    dry_run = dry_run or False
    await _ou_edit_parent(uuid, new_parent, at, dry_run=dry_run)
    return {"status": "OK"}
