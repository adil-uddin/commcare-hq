# Generated by Django 1.11.11 on 2018-03-27 20:32
from corehq.sql_db.operations import RawSQLMigration
from django.db import migrations

from custom.icds_reports.const import SQL_TEMPLATES_ROOT

migrator = RawSQLMigration((SQL_TEMPLATES_ROOT,))


class Migration(migrations.Migration):

    dependencies = [
        ('icds_reports', '0036_allow_null_for_pnc_tables'),
    ]

    operations = [
        migrator.get_migration('update_tables18.sql'),
    ]
