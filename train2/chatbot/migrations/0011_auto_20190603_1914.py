# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2019-06-03 16:14
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0010_auto_20190603_1913'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatreport',
            name='full_trip',
            field=django.contrib.postgres.fields.jsonb.JSONField(),
        ),
        migrations.AlterField(
            model_name='chatreport',
            name='session',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='report', to='chatbot.ChatSession'),
        ),
        migrations.AlterField(
            model_name='chatreport',
            name='user_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(),
        ),
    ]