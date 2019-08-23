# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-27 20:57

from architect.commands import partition
from django.db import migrations, models

from corehq.util.django_migrations import add_if_not_exists_raw


def add_partitions(apps, schema_editor):
    partition.run({'module': 'phonelog.models'})


class Migration(migrations.Migration):

    dependencies = [
        ('phonelog', '0010_rename_device_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceReportEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('xform_id', models.CharField(db_index=True, max_length=50)),
                ('i', models.IntegerField()),
                ('msg', models.TextField()),
                ('type', models.CharField(max_length=32)),
                ('date', models.DateTimeField()),
                ('server_date', models.DateTimeField(db_index=True, null=True)),
                ('domain', models.CharField(max_length=100)),
                ('device_id', models.CharField(max_length=50, null=True)),
                ('app_version', models.TextField(null=True)),
                ('username', models.CharField(max_length=100, null=True)),
                ('user_id', models.CharField(max_length=50, null=True)),
            ],
            options={
                'db_table': 'phonelog_daily_partitioned_devicereportentry',
            },
        ),
        migrations.AlterUniqueTogether(
            name='devicereportentry',
            unique_together=set([('xform_id', 'i')]),
        ),
        migrations.AlterIndexTogether(
            name='devicereportentry',
            index_together=set(
                [('domain', 'device_id'), ('domain', 'date'), ('domain', 'type'), ('domain', 'username')]
            ),
        ),
        migrations.RunSQL(
            add_if_not_exists_raw(
                """
                CREATE INDEX devicereportentry_domain_device_id_pattern_ops
                ON phonelog_daily_partitioned_devicereportentry (domain, device_id varchar_pattern_ops)
                """, name='phonelog_daily_partitioned_devicereportentry_domain_device_id_pattern_ops'
            ),
            reverse_sql=
            """
            DROP INDEX IF EXISTS devicereportentry_domain_device_id_pattern_ops
            """,
        ),
        migrations.RunPython(add_partitions),
    ]
