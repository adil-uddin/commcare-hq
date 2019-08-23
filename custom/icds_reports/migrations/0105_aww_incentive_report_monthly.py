# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-03-12 10:52

from django.db import migrations

from corehq.sql_db.operations import RawSQLMigration

migrator = RawSQLMigration(('custom', 'icds_reports', 'migrations', 'sql_templates', 'database_views'))


class Migration(migrations.Migration):

    dependencies = [
        ('icds_reports', '0104_agg_ls_monthly_ls_name'),
    ]

    operations = [
        migrator.get_migration('aww_incentive_report_monthly.sql'),
    ]
