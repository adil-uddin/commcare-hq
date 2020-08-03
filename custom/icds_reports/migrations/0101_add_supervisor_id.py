# Generated by Django 1.11.20 on 2019-03-01 10:41
from corehq.sql_db.operations import RawSQLMigration
from django.db import migrations, models

from custom.icds_reports.const import SQL_TEMPLATES_ROOT

migrator = RawSQLMigration((SQL_TEMPLATES_ROOT,))


class Migration(migrations.Migration):

    dependencies = [
        ('icds_reports', '0100_add_supervisor_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='aggregateawcinfrastructureforms',
            name='supervisor_id',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='aggregatechildhealthdailyfeedingforms',
            name='supervisor_id',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='aggregatechildhealthpostnatalcareforms',
            name='supervisor_id',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='aggregatechildhealththrforms',
            name='supervisor_id',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='aggregategrowthmonitoringforms',
            name='supervisor_id',
            field=models.TextField(null=True),
        ),
        migrator.get_migration('update_tables43.sql')
    ]
