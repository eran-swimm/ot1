# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-03-30 09:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0003_auto_20190318_2204'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatsession',
            name='current_step',
            field=models.CharField(default='initial', max_length=50),
        ),
    ]