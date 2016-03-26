# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-26 12:52
from __future__ import unicode_literals

import common.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Route',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stop_ids', common.fields.ArrayField()),
            ],
        ),
        migrations.CreateModel(
            name='Sample',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_source', models.BooleanField(default=False)),
                ('is_dest', models.BooleanField(default=False)),
                ('actual_arrival', models.DateTimeField(null=True)),
                ('exp_arrival', models.DateTimeField(null=True)),
                ('actual_departure', models.DateTimeField(null=True)),
                ('exp_departure', models.DateTimeField(null=True)),
                ('index', models.IntegerField()),
                ('filename', models.CharField(max_length=500)),
                ('line_number', models.IntegerField()),
                ('valid', models.BooleanField(db_index=True, default=True)),
                ('invalid_reason', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Stop',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gtfs_stop_id', models.IntegerField(db_index=True, unique=True)),
                ('english', models.CharField(max_length=50)),
                ('hebrews', common.fields.ArrayField()),
                ('lat', models.FloatField()),
                ('lon', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Trip',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('train_num', models.IntegerField(db_index=True)),
                ('date', models.DateField(db_index=True)),
                ('valid', models.BooleanField(db_index=True, default=True)),
                ('invalid_reason', models.TextField(blank=True, null=True)),
                ('route', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='trips', to='data.Route')),
            ],
        ),
        migrations.AddField(
            model_name='sample',
            name='stop',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='samples', to='data.Stop'),
        ),
        migrations.AddField(
            model_name='sample',
            name='trip',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='samples', to='data.Trip'),
        ),
        migrations.AlterUniqueTogether(
            name='trip',
            unique_together=set([('train_num', 'date')]),
        ),
        migrations.AlterUniqueTogether(
            name='sample',
            unique_together=set([('trip', 'stop'), ('trip', 'index'), ('filename', 'line_number')]),
        ),
    ]
