# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import saleor.registration.models


class Migration(migrations.Migration):

    replaces = [(b'registration', '0001_initial'), (b'registration', '0002_auto_20151203_1158')]

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailChangeRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('token', models.CharField(unique=True, max_length=36)),
                ('valid_until', models.DateTimeField(default=saleor.registration.models.default_valid_date)),
                ('email', models.EmailField(max_length=254)),
                ('user', models.ForeignKey(related_name='email_change_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EmailConfirmationRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('token', models.CharField(unique=True, max_length=36)),
                ('valid_until', models.DateTimeField(default=saleor.registration.models.default_valid_date)),
                ('email', models.EmailField(max_length=254)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ExternalUserData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('service', models.CharField(max_length=255, db_index=True)),
                ('username', models.CharField(max_length=255, db_index=True)),
                ('user', models.ForeignKey(related_name='external_ids', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='externaluserdata',
            unique_together=set([('service', 'username')]),
        ),
    ]
