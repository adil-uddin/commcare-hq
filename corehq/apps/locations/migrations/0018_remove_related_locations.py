# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-02-12 22:56
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0017_locationrelation_last_modified'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='locationrelation',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='locationrelation',
            name='location_a',
        ),
        migrations.RemoveField(
            model_name='locationrelation',
            name='location_b',
        ),
        migrations.AlterModelManagers(
            name='sqllocation',
            managers=[
            ],
        ),
        migrations.DeleteModel(
            name='LocationRelation',
        ),
    ]
