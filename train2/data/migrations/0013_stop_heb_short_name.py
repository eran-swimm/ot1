# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-13 18:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0012_remove_stop_hebrews'),
    ]

    operations = [
        migrations.AddField(
            model_name='stop',
            name='heb_short_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
