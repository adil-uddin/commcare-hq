# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-06-17 15:38

from django.db import migrations

from corehq.sql_db.operations import RawSQLMigration

migrator = RawSQLMigration(('custom', 'icds_reports', 'migrations', 'sql_templates'))


class Migration(migrations.Migration):

    dependencies = [
        ('icds_reports', '0122_incentive_columns'),
    ]

    operations = [
        migrator.get_migration('update_tables46.sql')
    ]
