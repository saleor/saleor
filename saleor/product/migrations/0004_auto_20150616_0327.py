# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import django_prices.models
import django.core.validators
import satchless.item


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0003_auto_20150610_0554'),
    ]

    operations = [
        migrations.CreateModel(
            name='GenericProduct',
            fields=[
                ('product_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='product.Product')),
                ('weight', models.DecimalField(max_digits=6, decimal_places=2)),
                ('price', django_prices.models.PriceField(currency=b'USD', verbose_name='price', max_digits=12, decimal_places=4)),
            ],
            bases=('product.product', models.Model),
        ),
        migrations.CreateModel(
            name='GenericVariant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stock', models.IntegerField(default=Decimal('1'), verbose_name='stock', validators=[django.core.validators.MinValueValidator(0)])),
                ('sku', models.CharField(unique=True, max_length=32, verbose_name='SKU')),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('product', models.ForeignKey(related_name='variants', to='product.GenericProduct')),
            ],
            bases=(models.Model, satchless.item.StockedItem, satchless.item.Item),
        ),
        migrations.RemoveField(
            model_name='bag',
            name='depth',
        ),
        migrations.RemoveField(
            model_name='bag',
            name='length',
        ),
        migrations.RemoveField(
            model_name='bag',
            name='width',
        ),
        migrations.RemoveField(
            model_name='shirt',
            name='depth',
        ),
        migrations.RemoveField(
            model_name='shirt',
            name='length',
        ),
        migrations.RemoveField(
            model_name='shirt',
            name='width',
        ),
        migrations.AlterField(
            model_name='product',
            name='categories',
            field=models.ManyToManyField(related_name='products', verbose_name='categories', to='product.Category'),
        ),
        migrations.AlterField(
            model_name='productimage',
            name='alt',
            field=models.CharField(max_length=128, verbose_name='short description', blank=True),
        ),
    ]
