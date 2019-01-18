# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-12-21 10:56
# pylint: disable=invalid-name,too-few-public-methods
"""Migration for the update of the DbLog table. Addition of uuids"""

from __future__ import unicode_literals
from __future__ import absolute_import

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.db import migrations, models
from aiida.backends.djsite.db.migrations import upgrade_schema_version
import aiida.common.utils

REVISION = '1.0.24'
DOWN_REVISION = '1.0.23'


class Migration(migrations.Migration):
    """
    This migration updated the DbLog schema and adds UUID for correct export of the DbLog entries.
    """

    dependencies = [
        ('db', '0023_calc_job_option_attribute_keys'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dblog',
            name='objpk',
        ),
        migrations.AddField(
            model_name='dblog',
            name='objuuid',
            field=models.UUIDField(db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='dblog',
            name='uuid',
            field=models.UUIDField(default=aiida.common.utils.get_new_uuid, unique=True),
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
