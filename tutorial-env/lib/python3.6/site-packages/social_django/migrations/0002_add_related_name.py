# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings

from social_core.utils import setting_name

USER_MODEL = getattr(settings, setting_name('USER_MODEL'), None) or \
             getattr(settings, 'AUTH_USER_MODEL', None) or \
             'auth.User'


class Migration(migrations.Migration):
    replaces = [
        ('default', '0002_add_related_name'),
        ('social_auth', '0002_add_related_name')
    ]

    dependencies = [
        ('social_django', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersocialauth',
            name='user',
            field=models.ForeignKey(
                related_name='social_auth', to=USER_MODEL, on_delete=models.CASCADE,
            )
        ),
    ]
