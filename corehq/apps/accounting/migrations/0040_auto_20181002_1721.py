# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-10-02 17:21

from django.db import migrations
from corehq.apps.accounting.bootstrap.config.standard_user_limit_october_2018 import BOOTSTRAP_CONFIG
from corehq.apps.accounting.bootstrap.utils import ensure_plans



def noop(*args, **kwargs):
    pass


def _bootstrap_new_monthly_pricing(apps, schema_editor):
    ensure_plans(BOOTSTRAP_CONFIG, verbose=True, apps=apps)


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0039_auto_20180828_2258'),
    ]

    operations = [
        migrations.RunPython(_bootstrap_new_monthly_pricing, reverse_code=noop)
    ]
