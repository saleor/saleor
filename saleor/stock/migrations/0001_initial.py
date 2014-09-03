# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'StockRecord'
        db.create_table(u'stock_stockrecord', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sku', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32)),
            ('in_stock', self.gf('django.db.models.fields.IntegerField')()),
            ('price', self.gf('django_prices.models.PriceField')(currency='AED', max_digits=12, decimal_places=4)),
            ('allow_overselling', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'stockrecords', to=orm['product.Product'])),
        ))
        db.send_create_signal(u'stock', ['StockRecord'])


    def backwards(self, orm):
        # Deleting model 'StockRecord'
        db.delete_table(u'stock_stockrecord')


    models = {
        u'product.brand': {
            'Meta': {'object_name': 'Brand'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'null': 'True'})
        },
        u'product.category': {
            'Meta': {'object_name': 'Category'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            u'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'children'", 'null': 'True', 'to': u"orm['product.Category']"}),
            u'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            u'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        u'product.product': {
            'Meta': {'object_name': 'Product'},
            'brand': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['product.Brand']"}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'products'", 'to': u"orm['product.Category']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_organic': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '128', 'blank': 'True'}),
            'package_size': ('django.db.models.fields.IntegerField', [], {}),
            'sku': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'unit_value': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '2'})
        },
        u'stock.stockrecord': {
            'Meta': {'object_name': 'StockRecord'},
            'allow_overselling': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_stock': ('django.db.models.fields.IntegerField', [], {}),
            'price': ('django_prices.models.PriceField', [], {'currency': "'AED'", 'max_digits': '12', 'decimal_places': '4'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'stockrecords'", 'to': u"orm['product.Product']"}),
            'sku': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'})
        }
    }

    complete_apps = ['stock']