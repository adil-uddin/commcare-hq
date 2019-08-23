# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-02-22 20:08

from django.db import migrations
from django.core.management import call_command

from corehq.privileges import RESTRICT_ACCESS_BY_LOCATION


def _grandfather_location(apps, schema_editor):
    call_command(
        'cchq_prbac_grandfather_privs',
        RESTRICT_ACCESS_BY_LOCATION,
        skip_edition='Community,Standard',
        noinput=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0001_squashed_0052_ensure_report_builder_plans'),
    ]

    operations = [
        migrations.RunPython(_grandfather_location),
    ]
