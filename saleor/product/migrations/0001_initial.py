# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import versatileimagefield.fields
import django_prices.models
import django.core.validators
import satchless.item


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BagVariant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stock', models.IntegerField(default=Decimal('1'), verbose_name='stock', validators=[django.core.validators.MinValueValidator(0)])),
                ('sku', models.CharField(unique=True, max_length=32, verbose_name='SKU')),
            ],
            bases=(models.Model, satchless.item.StockedItem, satchless.item.Item),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128, verbose_name='name')),
                ('slug', models.SlugField(unique=True, verbose_name='slug')),
                ('description', models.TextField(verbose_name='description', blank=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', models.ForeignKey(related_name='children', verbose_name='parent', blank=True, to='product.Category', null=True)),
            ],
            options={
                'verbose_name_plural': 'categories',
            },
        ),
        migrations.CreateModel(
            name='Color',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('color', models.CharField(max_length=6, verbose_name='HEX value')),
            ],
        ),
        migrations.CreateModel(
            name='FixedProductDiscount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('discount', django_prices.models.PriceField(currency=b'USD', verbose_name='discount value', max_digits=12, decimal_places=4)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128, verbose_name='name')),
                ('description', models.TextField(verbose_name='description')),
                ('collection', models.CharField(db_index=True, max_length=100, blank=True)),
            ],
            bases=(models.Model, satchless.item.ItemRange),
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', versatileimagefield.fields.VersatileImageField(upload_to='products')),
                ('ppoi', versatileimagefield.fields.PPOIField(default='0.5x0.5', max_length=20, editable=False)),
                ('alt', models.CharField(max_length=128, verbose_name='alternative text', blank=True)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='ShirtVariant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stock', models.IntegerField(default=Decimal('1'), verbose_name='stock', validators=[django.core.validators.MinValueValidator(0)])),
                ('sku', models.CharField(unique=True, max_length=32, verbose_name='SKU')),
                ('size', models.CharField(max_length=3, verbose_name='size', choices=[('xs', 'XS'), ('s', 'S'), ('m', 'M'), ('l', 'L'), ('xl', 'XL'), ('xxl', 'XXL')])),
            ],
            bases=(models.Model, satchless.item.StockedItem, satchless.item.Item),
        ),
        migrations.CreateModel(
            name='Bag',
            fields=[
                ('product_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='product.Product')),
                ('weight', models.DecimalField(max_digits=6, decimal_places=2)),
                ('length', models.DecimalField(default=0, max_digits=6, decimal_places=2, blank=True)),
                ('width', models.DecimalField(default=0, max_digits=6, decimal_places=2, blank=True)),
                ('depth', models.DecimalField(default=0, max_digits=6, decimal_places=2, blank=True)),
                ('price', django_prices.models.PriceField(currency=b'USD', verbose_name='price', max_digits=12, decimal_places=4)),
                ('color', models.ForeignKey(to='product.Color')),
            ],
            bases=('product.product', models.Model),
        ),
        migrations.CreateModel(
            name='Shirt',
            fields=[
                ('product_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='product.Product')),
                ('weight', models.DecimalField(max_digits=6, decimal_places=2)),
                ('length', models.DecimalField(default=0, max_digits=6, decimal_places=2, blank=True)),
                ('width', models.DecimalField(default=0, max_digits=6, decimal_places=2, blank=True)),
                ('depth', models.DecimalField(default=0, max_digits=6, decimal_places=2, blank=True)),
                ('price', django_prices.models.PriceField(currency=b'USD', verbose_name='price', max_digits=12, decimal_places=4)),
                ('color', models.ForeignKey(to='product.Color')),
            ],
            bases=('product.product', models.Model),
        ),
        migrations.AddField(
            model_name='productimage',
            name='product',
            field=models.ForeignKey(related_name='images', to='product.Product'),
        ),
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(related_name='products', verbose_name='category', to='product.Category'),
        ),
        migrations.AddField(
            model_name='fixedproductdiscount',
            name='products',
            field=models.ManyToManyField(to='product.Product', blank=True),
        ),
        migrations.AddField(
            model_name='shirtvariant',
            name='product',
            field=models.ForeignKey(related_name='variants', to='product.Shirt'),
        ),
        migrations.AddField(
            model_name='bagvariant',
            name='product',
            field=models.ForeignKey(related_name='variants', to='product.Bag'),
        ),
    ]
