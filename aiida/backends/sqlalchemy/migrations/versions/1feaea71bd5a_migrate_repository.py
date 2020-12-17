# -*- coding: utf-8 -*-
# pylint: disable=invalid-name,no-member
"""Migrate the file repository to the new disk object store based implementation.

Revision ID: 1feaea71bd5a
Revises: 7536a82b2cc4
Create Date: 2020-10-01 15:05:49.271958

"""
from alembic import op
from sqlalchemy import Integer, cast
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import table, column, select, func

from aiida.backends.general.migrations import utils
from aiida.cmdline.utils import echo

# revision identifiers, used by Alembic.
revision = '1feaea71bd5a'
down_revision = '7536a82b2cc4'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    import json
    import tempfile
    from aiida.manage.configuration import get_profile

    connection = op.get_bind()

    DbNode = table(
        'db_dbnode',
        column('id', Integer),
        column('uuid', UUID),
        column('repository_metadata', JSONB),
    )

    profile = get_profile()
    node_count = connection.execute(select([func.count()]).select_from(DbNode)).scalar()
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

            value = cast(repository_metadata, JSONB)
            connection.execute(DbNode.update().where(DbNode.c.uuid == node_uuid).values(repository_metadata=value))

        del mapping_node_repository_metadata

    if not profile.is_test_profile:

        if missing_repo_folder:
            prefix = 'migration-repository-missing-subfolder-'
            with tempfile.NamedTemporaryFile(prefix=prefix, suffix='.json', dir='.', mode='w+', delete=False) as handle:
                json.dump(missing_repo_folder, handle)
                echo.echo_warning(
                    'Detected node repository folders that were missing the required subfolder `path` or `raw_input`. '
                    f'The paths of those nodes repository folders have been written to a log file: {handle.name}'
                )

        # If there were no nodes, most likely a new profile, there is not need to print the warning
        if node_count:
            import pathlib
            echo.echo_warning(
                'Migrated the file repository to the new disk object store. The old repository has not been deleted out'
                f' of safety and can be found at {pathlib.Path(get_profile().repository_path, "repository")}.'
            )


def downgrade():
    """Migrations for the downgrade."""
