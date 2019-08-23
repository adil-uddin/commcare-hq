# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-26 14:19

import corehq.warehouse.etl
import corehq.warehouse.models.shared
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0004_app_status_fact_form_fact_form_staging_synclog_staging_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='LocationStagingTable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=255)),
                ('site_code', models.CharField(max_length=100)),
                ('location_id', models.CharField(max_length=255)),
                ('location_type_id', models.IntegerField()),
                ('external_id', models.CharField(max_length=255, null=True)),
                ('supply_point_id', models.CharField(max_length=255, null=True)),
                ('user_id', models.CharField(max_length=255)),
                ('sql_location_id', models.IntegerField()),
                ('sql_parent_location_id', models.IntegerField(null=True)),
                ('location_last_modified', models.DateTimeField(null=True)),
                ('location_created_on', models.DateTimeField(null=True)),
                ('is_archived', models.NullBooleanField()),
                ('latitude', models.DecimalField(decimal_places=10, max_digits=20, null=True)),
                ('longitude', models.DecimalField(decimal_places=10, max_digits=20, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, corehq.warehouse.models.shared.WarehouseTable, corehq.warehouse.etl.CustomSQLETLMixin),
        ),
        migrations.CreateModel(
            name='LocationTypeStagingTable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=255)),
                ('code', models.SlugField(db_index=False, null=True)),
                ('location_type_id', models.IntegerField()),
                ('location_type_last_modified', models.DateTimeField(null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, corehq.warehouse.models.shared.WarehouseTable, corehq.warehouse.etl.CustomSQLETLMixin),
        ),
        migrations.AddField(
            model_name='locationdim',
            name='level',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='locationdim',
            name='location_level_0',
            field=models.IntegerField(db_index=True, default=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='locationdim',
            name='location_level_1',
            field=models.IntegerField(db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='locationdim',
            name='location_level_2',
            field=models.IntegerField(db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='locationdim',
            name='location_level_3',
            field=models.IntegerField(db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='locationdim',
            name='location_level_4',
            field=models.IntegerField(db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='locationdim',
            name='location_level_5',
            field=models.IntegerField(db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='locationdim',
            name='location_level_6',
            field=models.IntegerField(db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='locationdim',
            name='location_level_7',
            field=models.IntegerField(db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='locationdim',
            name='sql_location_id',
            field=models.IntegerField(default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='locationdim',
            name='external_id',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='locationdim',
            name='is_archived',
            field=models.NullBooleanField(),
        ),
        migrations.AlterField(
            model_name='locationdim',
            name='location_created_on',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='locationdim',
            name='location_type_id',
            field=models.IntegerField(),
        ),
    ]
