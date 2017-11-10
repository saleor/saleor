# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import versatileimagefield.fields
from decimal import Decimal
import django.core.validators
import django_prices.models
import satchless.item


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AttributeChoiceValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('display', models.CharField(max_length=100, verbose_name='display name')),
                ('color', models.CharField(blank=True, max_length=7, verbose_name='color', validators=[django.core.validators.RegexValidator('^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')])),
                ('image', versatileimagefield.fields.VersatileImageField(upload_to='attributes', null=True, verbose_name='image', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128, verbose_name='name')),
                ('slug', models.SlugField(verbose_name='slug')),
                ('description', models.TextField(verbose_name='description', blank=True)),
                ('hidden', models.BooleanField(default=False, verbose_name='hidden')),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', models.ForeignKey(related_name='children', verbose_name='parent', blank=True, to='product.Category', null=True, on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'categories',
            },
        ),
        migrations.CreateModel(
            name='FixedProductDiscount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('discount', django_prices.models.PriceField(currency=b'USD', verbose_name='discount value', max_digits=12, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128, verbose_name='name')),
                ('description', models.TextField(verbose_name='description')),
                ('price', django_prices.models.PriceField(currency=b'USD', verbose_name='price', max_digits=12, decimal_places=2)),
                ('weight', models.DecimalField(verbose_name='weight', max_digits=6, decimal_places=2)),
                ('available_on', models.DateField(null=True, verbose_name='available on', blank=True)),
            ],
            bases=(models.Model, satchless.item.ItemRange),
        ),
        migrations.CreateModel(
            name='ProductAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.SlugField(unique=True, verbose_name='internal name')),
                ('display', models.CharField(max_length=100, verbose_name='display name')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', versatileimagefield.fields.VersatileImageField(upload_to='products')),
                ('ppoi', versatileimagefield.fields.PPOIField(default='0.5x0.5', max_length=20, editable=False)),
                ('alt', models.CharField(max_length=128, verbose_name='short description', blank=True)),
                ('order', models.PositiveIntegerField(editable=False)),
                ('product', models.ForeignKey(related_name='images', to='product.Product', on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sku', models.CharField(unique=True, max_length=32, verbose_name='SKU')),
                ('name', models.CharField(max_length=100, verbose_name='variant name', blank=True)),
                ('price_override', django_prices.models.PriceField(decimal_places=2, currency=b'USD', max_digits=12, blank=True, null=True, verbose_name='price override')),
                ('weight_override', models.DecimalField(decimal_places=2, max_digits=6, blank=True, null=True, verbose_name='weight override')),
                ('attributes', models.TextField(default='{}', verbose_name='attributes')),
                ('product', models.ForeignKey(related_name='variants', to='product.Product', on_delete=django.db.models.deletion.CASCADE)),
            ],
            bases=(models.Model, satchless.item.Item),
        ),
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('location', models.CharField(max_length=100, verbose_name='location')),
                ('quantity', models.IntegerField(default=Decimal('1'), verbose_name='quantity', validators=[django.core.validators.MinValueValidator(0)])),
                ('cost_price', django_prices.models.PriceField(decimal_places=2, currency=b'USD', max_digits=12, blank=True, null=True, verbose_name='cost price')),
                ('variant', models.ForeignKey(related_name='stock', verbose_name='variant', to='product.ProductVariant', on_delete=django.db.models.deletion.CASCADE)),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='attributes',
            field=models.ManyToManyField(related_name='products', null=True, to='product.ProductAttribute', blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='categories',
            field=models.ManyToManyField(related_name='products', verbose_name='categories', to='product.Category'),
        ),
        migrations.AddField(
            model_name='fixedproductdiscount',
            name='products',
            field=models.ManyToManyField(to='product.Product', blank=True),
        ),
        migrations.AddField(
            model_name='attributechoicevalue',
            name='attribute',
            field=models.ForeignKey(related_name='values', to='product.ProductAttribute', on_delete=django.db.models.deletion.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='stock',
            unique_together=set([('variant', 'location')]),
        ),
    ]
