# Generated by Django 2.2.16 on 2020-11-17 19:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0051_hubspot_restrictions'),
        ('export', '0009_incrementalexport_incrementalexportcheckpoint'),
    ]

    operations = [
        migrations.CreateModel(
            name='DefaultExportSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('forms_filetype', models.CharField(choices=[('CSV', 'CSV (zip file)'),
                                                             ('EXCEL_2007_PLUS', 'Excel 2007+'),
                                                             ('EXCEL_PRE_2007', 'Excel (older versions)')],
                                                    default='EXCEL_2007_PLUS', max_length=25)),
                ('forms_auto_convert', models.BooleanField(default=True)),
                ('forms_auto_format_cells', models.BooleanField(default=False)),
                ('forms_include_duplicates', models.BooleanField(default=False)),
                ('forms_expand_checkbox', models.BooleanField(default=False)),
                ('cases_filetype', models.CharField(choices=[('CSV', 'CSV (zip file)'),
                                                             ('EXCEL_2007_PLUS', 'Excel 2007+'),
                                                             ('EXCEL_PRE_2007', 'Excel (older versions)')],
                                                    default='EXCEL_2007_PLUS', max_length=25)),
                ('cases_auto_convert', models.BooleanField(default=True)),
                ('odata_include_duplicates', models.BooleanField(default=False)),
                ('odata_expand_checkbox', models.BooleanField(default=False)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              to='accounting.BillingAccount')),
            ],
        ),
    ]
