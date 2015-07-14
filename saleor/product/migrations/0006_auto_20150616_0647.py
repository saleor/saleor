# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import django_prices.models
import django.core.validators
import satchless.item


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0005_auto_20150616_0354'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('sku', models.CharField(max_length=32, verbose_name='SKU')),
                ('price', django_prices.models.PriceField(decimal_places=4, currency=b'USD', max_digits=12, blank=True, null=True, verbose_name='price')),
            ],
            bases=(models.Model, satchless.item.Item),
        ),
        migrations.RemoveField(
            model_name='genericproduct',
            name='price',
        ),
        migrations.RemoveField(
            model_name='genericvariant',
            name='id',
        ),
        migrations.RemoveField(
            model_name='genericvariant',
            name='name',
        ),
        migrations.RemoveField(
            model_name='genericvariant',
            name='product',
        ),
        migrations.RemoveField(
            model_name='genericvariant',
            name='sku',
        ),
        migrations.AddField(
            model_name='genericproduct',
            name='stock',
            field=models.IntegerField(default=Decimal('1'), verbose_name='stock', validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='product',
            name='price',
            field=django_prices.models.PriceField(default=0, currency=b'USD', verbose_name='price', max_digits=12, decimal_places=4),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='sku',
            field=models.CharField(default='', max_length=32, verbose_name='SKU'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='productvariant',
            name='product',
            field=models.ForeignKey(related_name='variants', to='product.Product'),
        ),
        migrations.AddField(
            model_name='genericvariant',
            name='productvariant_ptr',
            field=models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, default='', serialize=False, to='product.ProductVariant'),
            preserve_default=False,
        ),
    ]
