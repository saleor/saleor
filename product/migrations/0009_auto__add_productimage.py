# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ProductImage'
        db.create_table(u'product_productimage', (
            (u'image_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['django_images.Image'], unique=True, primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(related_name='images', to=orm['product.Product'])),
        ))
        db.send_create_signal(u'product', ['ProductImage'])


    def backwards(self, orm):
        # Deleting model 'ProductImage'
        db.delete_table(u'product_productimage')


    models = {
        u'django_images.image': {
            'Meta': {'object_name': 'Image'},
            'height': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '255'}),
            'width': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
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
        u'product.fixedproductdiscount': {
            'Meta': {'object_name': 'FixedProductDiscount'},
            'discount': ('django_prices.models.PriceField', [], {'currency': "'USD'", 'max_digits': '12', 'decimal_places': '4'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'products': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['product.Product']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'product.product': {
            'Meta': {'object_name': 'Product'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'products'", 'to': u"orm['product.Category']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'price': ('django_prices.models.PriceField', [], {'currency': "'USD'", 'max_digits': '12', 'decimal_places': '4'}),
            'sku': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'})
        },
        u'product.productimage': {
            'Meta': {'ordering': "['id']", 'object_name': 'ProductImage', '_ormbases': [u'django_images.Image']},
            u'image_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['django_images.Image']", 'unique': 'True', 'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'images'", 'to': u"orm['product.Product']"})
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