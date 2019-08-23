# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-05-08 19:52

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0024_unique__transaction_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='billingrecord',
            name='emailed_to_list',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.EmailField(max_length=254),
                                                            default=list, size=None),
        ),
        migrations.AddField(
            model_name='wirebillingrecord',
            name='emailed_to_list',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.EmailField(max_length=254),
                                                            default=list, size=None),
        ),
    ]
