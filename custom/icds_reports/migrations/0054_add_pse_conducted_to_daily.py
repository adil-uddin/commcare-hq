# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-07-18 17:45

from django.db import migrations

from corehq.sql_db.operations import RawSQLMigration

migrator = RawSQLMigration(('custom', 'icds_reports', 'migrations', 'sql_templates'))


class Migration(migrations.Migration):

    dependencies = [
        ('icds_reports', '0053_aggregatechildhealthdailyfeedingforms'),
    ]

    operations = [
        migrator.get_migration('update_tables24.sql'),
    ]
