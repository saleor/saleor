# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ImpersonationLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('session_key', models.CharField(help_text='The Django session request key.', max_length=40)),
                ('session_started_at', models.DateTimeField(help_text='The time impersonation began.', null=True, blank=True)),
                ('session_ended_at', models.DateTimeField(help_text='The time impersonation ended.', null=True, blank=True)),
                ('impersonating', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='impersonated_by', to=settings.AUTH_USER_MODEL, help_text='The user being impersonated.')),
                ('impersonator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='impersonations', to=settings.AUTH_USER_MODEL, help_text='The user doing the impersonating.')),
            ],
        ),
    ]
