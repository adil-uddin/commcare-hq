# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-08-31 18:21

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_add_location_permission'),
    ]

    operations = [
        migrations.CreateModel(
            name='DomainRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.CharField(db_index=True, max_length=100)),
                ('full_name', models.CharField(db_index=True, max_length=100)),
                ('is_approved', models.BooleanField(default=False)),
                ('domain', models.CharField(db_index=True, max_length=255)),
            ],
        ),
    ]
