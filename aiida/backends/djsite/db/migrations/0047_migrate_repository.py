# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,too-few-public-methods
"""Migrate the file repository to the new disk object store based implementation."""
# pylint: disable=no-name-in-module,import-error
from django.core.exceptions import ObjectDoesNotExist
from django.db import migrations

from aiida.backends.djsite.db.migrations import upgrade_schema_version
from aiida.backends.general.migrations import utils
from aiida.cmdline.utils import echo

REVISION = '1.0.47'
DOWN_REVISION = '1.0.46'


def migrate_repository(apps, _):
    """Migrate the repository."""
    import json
    import tempfile
    from aiida.manage.configuration import get_profile

    DbNode = apps.get_model('db', 'DbNode')

    profile = get_profile()
    node_count = DbNode.objects.count()
    missing_node_uuids = []
    missing_repo_folder = []

    for i in range(256):

        shard = '%.2x' % i  # noqa flynt
        mapping_node_repository_metadata, missing_sub_repo_folder = utils.migrate_legacy_repository(node_count, shard)

        if missing_sub_repo_folder:
            missing_repo_folder.extend(missing_sub_repo_folder)
            del missing_sub_repo_folder

        if mapping_node_repository_metadata is None:
            continue

        for node_uuid, repository_metadata in mapping_node_repository_metadata.items():

            # If `repository_metadata` is `{}` or `None`, we skip it, as we can leave the column default `null`.
            if not repository_metadata:
                continue

            try:
                # This can happen if the node was deleted but the repo folder wasn't, or the repo folder just never
                # corresponded to an actual node. In any case, we don't want to fail but just log the warning.
                node = DbNode.objects.get(uuid=node_uuid)
            except ObjectDoesNotExist:
                missing_node_uuids.append((node_uuid, repository_metadata))
            else:
                node.repository_metadata = repository_metadata
                node.save()

        del mapping_node_repository_metadata

    if not profile.is_test_profile:

        if missing_node_uuids:
            prefix = 'migration-repository-missing-nodes-'
            with tempfile.NamedTemporaryFile(prefix=prefix, suffix='.json', dir='.', mode='w+', delete=False) as handle:
                json.dump(missing_node_uuids, handle)
                echo.echo_warning(
                    '\nDetected node repository folders for nodes that do not exist in the database. The UUIDs of those'
                    f' nodes have been written to a log file: {handle.name}'
                )

        if missing_repo_folder:
            prefix = 'migration-repository-missing-subfolder-'
            with tempfile.NamedTemporaryFile(prefix=prefix, suffix='.json', dir='.', mode='w+', delete=False) as handle:
                json.dump(missing_repo_folder, handle)
                echo.echo_warning(
                    '\nDetected node repository folders that were missing the required subfolder `path` or `raw_input`.'
                    f' The paths of those nodes repository folders have been written to a log file: {handle.name}'
                )

        # If there were no nodes, most likely a new profile, there is not need to print the warning
        if node_count:
            import pathlib
            echo.echo_warning(
                '\nMigrated the file repository to the new disk object store. The old repository has not been deleted '
                f'out of safety and can be found at {pathlib.Path(profile.repository_path, "repository")}.'
            )


class Migration(migrations.Migration):
    """Migrate the file repository to the new disk object store based implementation."""

    dependencies = [
        ('db', '0046_add_node_repository_metadata'),
    ]

    operations = [
        migrations.RunPython(migrate_repository, reverse_code=migrations.RunPython.noop),
        upgrade_schema_version(REVISION, DOWN_REVISION),
    ]
