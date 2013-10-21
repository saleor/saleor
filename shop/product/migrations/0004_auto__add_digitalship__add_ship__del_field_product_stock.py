# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DigitalShip'
        db.create_table(u'product_digitalship', (
            (u'product_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['product.Product'], unique=True, primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal(u'product', ['DigitalShip'])

        # Adding model 'Ship'
        db.create_table(u'product_ship', (
            (u'product_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['product.Product'], unique=True, primary_key=True)),
            ('stock', self.gf('django.db.models.fields.DecimalField')(default='1', max_digits=10, decimal_places=4)),
            ('weight', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('length', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, blank=True)),
            ('width', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, blank=True)),
            ('depth', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, blank=True)),
        ))
        db.send_create_signal(u'product', ['Ship'])

        # Deleting field 'Product.stock'
        db.delete_column(u'product_product', 'stock')


    def backwards(self, orm):
        # Deleting model 'DigitalShip'
        db.delete_table(u'product_digitalship')

        # Deleting model 'Ship'
        db.delete_table(u'product_ship')

        # Adding field 'Product.stock'
        db.add_column(u'product_product', 'stock',
                      self.gf('django.db.models.fields.DecimalField')(default='1', max_digits=10, decimal_places=4),
                      keep_default=False)


    models = {
        u'product.category': {
            'Meta': {'object_name': 'Category'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['product.Category']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        u'product.digitalship': {
            'Meta': {'object_name': 'DigitalShip', '_ormbases': [u'product.Product']},
            u'product_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['product.Product']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'product.product': {
            'Meta': {'object_name': 'Product'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'products'", 'to': u"orm['product.Category']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'price': ('django_prices.models.PriceField', [], {'currency': "'USD'", 'max_digits': '12', 'decimal_places': '4'})
        },
        u'product.ship': {
            'Meta': {'object_name': 'Ship', '_ormbases': [u'product.Product']},
            'depth': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'length': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            u'product_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['product.Product']", 'unique': 'True', 'primary_key': 'True'}),
            'stock': ('django.db.models.fields.DecimalField', [], {'default': "'1'", 'max_digits': '10', 'decimal_places': '4'}),
            'weight': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'width': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'})
        }
    }

    complete_apps = ['product']