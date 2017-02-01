# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-31 13:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AWSServer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
                ('type', models.CharField(max_length=250)),
                ('state', models.CharField(max_length=250)),
                ('public_ip', models.CharField(max_length=250)),
                ('private_ip', models.CharField(max_length=250)),
                ('vpc', models.CharField(max_length=250)),
                ('server_price_by_hour', models.IntegerField(default=0)),
                ('volumes', models.CharField(max_length=250)),
                ('volumes_price', models.IntegerField(default=0)),
                ('cost_by_month', models.IntegerField(default=0)),
                ('launch_time', models.DateTimeField(blank=True)),
            ],
        ),
    ]
