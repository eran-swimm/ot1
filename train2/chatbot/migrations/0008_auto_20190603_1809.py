# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-06-03 15:09
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0007_chatreport_created_at'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='chatreport',
            options={'ordering': ('-created_at', '-id')},
        ),
    ]