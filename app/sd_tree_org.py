# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0

import asyncio
from collections import Counter
from functools import partial
from operator import itemgetter

from anytree import Node, RenderTree
from sd_connector import SDConnector

from app.config import Settings, get_settings


def create_sd_connector() -> SDConnector:
    settings: Settings = get_settings()

    sd_connector: SDConnector = SDConnector(
        settings.sd_institution,
        settings.sd_username,
        settings.sd_password,
        settings.sd_base_url,
    )
    return sd_connector


async def sd_tree_org(root_uuid=None):
    """Tool to print out the entire SD organization tree."""

    def build_parent_map(parent_map, department):
        uuid = department["DepartmentUUIDIdentifier"]
        if uuid in parent_map:
            return parent_map

        # Add ourselves to the parent map
        parent_map[uuid] = {
            "identifier": department["DepartmentIdentifier"],
            "level": department["DepartmentLevelIdentifier"],
            "parent": department.get("DepartmentReference", {}).get(
                "DepartmentUUIDIdentifier"
            ),
        }

        # Call recursively (if required)
        if "DepartmentReference" in department:
            parent_map = build_parent_map(parent_map, department["DepartmentReference"])
        return parent_map

    def find_children_uuids(tree, parent_uuid):
        children_uuids = [
            key for key, value in sorted(tree.items()) if value["parent"] == parent_uuid
        ]
        return children_uuids

    def build_any_tree(parent_map, root_uuid):
        def build_tree_node(uuid, parent=None):
            node = Node(
                department_name_map[uuid]
                + " ("
                + department_id_map[uuid]
                + ", "
                + uuid
                + ")",
                parent=parent,
            )
            return node

        def build_tree(parent_node, parent_uuid):
            node_uuids = find_children_uuids(parent_map, parent_uuid)
            for node_uuid in node_uuids:
                node = build_tree_node(node_uuid, parent=parent_node)
                build_tree(node, node_uuid)

        root = build_tree_node(root_uuid)
        build_tree(root, root_uuid)
        return root

    sd_connector = create_sd_connector()

    # Fire our requests
    responses = await asyncio.gather(
        sd_connector.getDepartment(), sd_connector.getOrganization()
    )
    department_response, organization_response = responses
    # Pull out the data
    departments = department_response["Department"]
    organization = organization_response["Organization"]["DepartmentReference"]

    # Generate map from UUID to Name for Deparments
    department_name_map = dict(
        map(itemgetter("DepartmentUUIDIdentifier", "DepartmentName"), departments)
    )
    department_id_map = dict(
        map(itemgetter("DepartmentUUIDIdentifier", "DepartmentIdentifier"), departments)
    )

    # Build parent map
    parent_map = {}
    for department in organization:
        parent_map = build_parent_map(parent_map, department)

    # Find roots of the parent_map
    if root_uuid:
        root_uuids = [str(root_uuid)]
    else:
        root_uuids = find_children_uuids(parent_map, None)

    # For each root, build an any-tree and print it
    output = ""
    trees = map(partial(build_any_tree, parent_map), root_uuids)
    for tree in trees:
        for pre, fill, node in RenderTree(tree):
            output += "%s%s" % (pre, node.name) + "\n"
        output += "\n"
    return output


async def department_identifier_list():
    sd_connector = create_sd_connector()
    department_response = await sd_connector.getDepartment()
    departments = department_response["Department"]
    department_identifiers = Counter(
        map(itemgetter("DepartmentIdentifier"), departments)
    )
    elements = {}
    for element, count in department_identifiers.most_common():
        if count == 1:  # We can break at 1, since most_common is ordered.
            break
        elements[element] = count
    return elements
