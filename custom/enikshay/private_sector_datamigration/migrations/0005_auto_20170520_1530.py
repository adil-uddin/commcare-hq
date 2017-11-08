# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-05-20 15:30
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('private_sector_datamigration', '0004_migratedbeneficiarycounter'),
    ]

    operations = [
        migrations.AlterField(
            model_name='episode',
            name='beneficiaryID',
            field=models.CharField(db_index=True, max_length=18),
        ),
        migrations.AlterField(
            model_name='episode',
            name='episodeDisplayID',
            field=models.IntegerField(db_index=True),
        ),
    ]
