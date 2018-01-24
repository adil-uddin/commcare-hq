# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-01-24 09:34
from __future__ import unicode_literals

from django.db import migrations, models

from corehq.sql_db.operations import HqRunSQL


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0016_readd_batch_key'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdim',
            name='domain',
            field=models.CharField(max_length=255, null=True),
        ),
        HqRunSQL(
            """
            ALTER TABLE warehouse_userdim
            ADD CONSTRAINT domain_conditional_null CHECK
            ((doc_type = 'WebUser' and domain IS NULL) OR (doc_type = 'CommCareUser' and domain is NOT NULL))
            """
        )
    ]
