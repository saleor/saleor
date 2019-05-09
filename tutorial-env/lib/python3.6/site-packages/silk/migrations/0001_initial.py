# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import uuid
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=300, blank=True, default='')),
                ('start_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('time_taken', models.FloatField(blank=True, null=True)),
                ('file_path', models.CharField(max_length=300, blank=True, default='')),
                ('line_num', models.IntegerField(blank=True, null=True)),
                ('end_line_num', models.IntegerField(blank=True, null=True)),
                ('func_name', models.CharField(max_length=300, blank=True, default='')),
                ('exception_raised', models.BooleanField(default=False)),
                ('dynamic', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Request',
            fields=[
                ('id', models.CharField(max_length=36, primary_key=True, default=uuid.uuid1, serialize=False)),
                ('path', models.CharField(db_index=True, max_length=190)),
                ('query_params', models.TextField(blank=True, default='')),
                ('raw_body', models.TextField(blank=True, default='')),
                ('body', models.TextField(blank=True, default='')),
                ('method', models.CharField(max_length=10)),
                ('start_time', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('view_name', models.CharField(db_index=True, blank=True, default='', max_length=190, null=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('time_taken', models.FloatField(blank=True, null=True)),
                ('encoded_headers', models.TextField(blank=True, default='')),
                ('meta_time', models.FloatField(blank=True, null=True)),
                ('meta_num_queries', models.IntegerField(blank=True, null=True)),
                ('meta_time_spent_queries', models.FloatField(blank=True, null=True)),
                ('pyprofile', models.TextField(blank=True, default='')),
                ('num_sql_queries', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.CharField(max_length=36, primary_key=True, default=uuid.uuid1, serialize=False)),
                ('status_code', models.IntegerField()),
                ('raw_body', models.TextField(blank=True, default='')),
                ('body', models.TextField(blank=True, default='')),
                ('encoded_headers', models.TextField(blank=True, default='')),
                ('request', models.OneToOneField(to='silk.Request', related_name='response', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='SQLQuery',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('query', models.TextField()),
                ('start_time', models.DateTimeField(default=django.utils.timezone.now, blank=True, null=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('time_taken', models.FloatField(blank=True, null=True)),
                ('traceback', models.TextField()),
                ('request', models.ForeignKey(to='silk.Request', blank=True, null=True, related_name='queries', on_delete=models.CASCADE)),
            ],
        ),
        migrations.AddField(
            model_name='profile',
            name='queries',
            field=models.ManyToManyField(to='silk.SQLQuery', db_index=True, related_name='profiles'),
        ),
        migrations.AddField(
            model_name='profile',
            name='request',
            field=models.ForeignKey(to='silk.Request', blank=True, null=True, on_delete=models.CASCADE),
        ),
    ]
