# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-08-27 09:20
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pillowtop', '0004_offset_to_big_int'),
    ]

    operations = [
        migrations.AddField(
            model_name='kafkacheckpoint',
            name='doc_modification_time',
            field=models.DateTimeField(null=True),
        ),
    ]
