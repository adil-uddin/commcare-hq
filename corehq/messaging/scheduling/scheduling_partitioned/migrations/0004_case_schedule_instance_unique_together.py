# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-22 16:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scheduling_partitioned', '0003_add_last_reset_case_property_value'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='casealertscheduleinstance',
            unique_together=set([('case_id', 'alert_schedule_id', 'recipient_type', 'recipient_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='casetimedscheduleinstance',
            unique_together=set([('case_id', 'timed_schedule_id', 'recipient_type', 'recipient_id')]),
        ),
    ]
