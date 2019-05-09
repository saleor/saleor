# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TaskResult',
            fields=[
                ('id', models.AutoField(auto_created=True,
                                        primary_key=True,
                                        serialize=False,
                                        verbose_name='ID')),
                ('task_id', models.CharField(
                    max_length=getattr(
                        settings,
                        'DJANGO_CELERY_RESULTS_TASK_ID_MAX_LENGTH',
                        255
                    ),
                    unique=True,
                    verbose_name='task id'
                )),
                ('status', models.CharField(choices=[('FAILURE', 'FAILURE'),
                                                     ('PENDING', 'PENDING'),
                                                     ('RECEIVED', 'RECEIVED'),
                                                     ('RETRY', 'RETRY'),
                                                     ('REVOKED', 'REVOKED'),
                                                     ('STARTED', 'STARTED'),
                                                     ('SUCCESS', 'SUCCESS')],
                                            default='PENDING',
                                            max_length=50,
                                            verbose_name='state')),
                ('content_type', models.CharField(
                    max_length=128, verbose_name='content type')),
                ('content_encoding', models.CharField(
                    max_length=64, verbose_name='content encoding')),
                ('result', models.TextField(default=None, editable=False,
                                            null=True)),
                ('date_done', models.DateTimeField(
                    auto_now=True, verbose_name='done at')),
                ('traceback', models.TextField(
                    blank=True, null=True, verbose_name='traceback')),
                ('hidden', models.BooleanField(
                    db_index=True, default=False, editable=False)),
                ('meta', models.TextField(default=None, editable=False,
                                          null=True)),
            ],
            options={
                'verbose_name': 'task result',
                'verbose_name_plural': 'task results',
            },
        ),
    ]
