# Generated by Django 2.2.13 on 2020-09-24 17:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('form_processor', '0091_auto_20190603_2023'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='casetransaction',
            name='fp_casetrans_formid_05e599_idx',
        ),
        migrations.AddIndex(
            model_name='casetransaction',
            index=models.Index(fields=['form_id'], name='form_proces_form_id_f2403a_idx'),
        ),
    ]
