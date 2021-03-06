# Generated by Django 2.2.16 on 2021-02-10 19:21

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hqwebapp', '0005_delete_apikeysettings'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAgent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(db_index=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='UserAccessLog',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('user_id', models.CharField(db_index=True, max_length=255)),
                ('action', models.CharField(choices=[('login', 'Login'), ('logout', 'Logout'),
                    ('failure', 'Login Failure')], max_length=20)),
                ('ip', models.GenericIPAddressField(blank=True, null=True)),
                ('path', models.CharField(blank=True, max_length=255)),
                ('timestamp', models.DateTimeField(default=datetime.datetime.utcnow)),
                ('user_agent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT,
                    to='hqwebapp.UserAgent')),
            ],
        ),
    ]
