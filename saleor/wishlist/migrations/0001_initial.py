# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.contrib.postgres.fields.hstore
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('product', '0028_merge_20170116_1016'),
    ]

    operations = [
        migrations.CreateModel(
            name='Wishlist',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('token', models.UUIDField(default=uuid.uuid4, unique=True, editable=False)),
                ('public', models.BooleanField(default=False)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='WishlistItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attributes', django.contrib.postgres.fields.hstore.HStoreField(default={})),
                ('watch', models.BooleanField(default=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(to='product.Product')),
                ('variant_object', models.ForeignKey(to='product.ProductVariant', null=True)),
                ('wishlist', models.ForeignKey(to='wishlist.Wishlist')),
            ],
        ),
        migrations.CreateModel(
            name='WishlistNotification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('variant', models.ForeignKey(to='product.ProductVariant')),
                ('wishlist', models.ForeignKey(to='wishlist.Wishlist')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='wishlistnotification',
            unique_together=set([('wishlist', 'variant')]),
        ),
        migrations.AlterUniqueTogether(
            name='wishlistitem',
            unique_together=set([('wishlist', 'product', 'variant_object', 'attributes')]),
        ),
    ]
