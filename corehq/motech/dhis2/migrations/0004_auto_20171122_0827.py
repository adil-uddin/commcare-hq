# Generated by Django 1.11.7 on 2017-11-22 08:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dhis2', '0003_jsonapilog_log_level'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jsonapilog',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
