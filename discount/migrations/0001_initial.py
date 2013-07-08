# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'SelectedProduct'
        db.create_table(u'discount_selectedproduct', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('discount', self.gf('django_prices.models.PriceField')(currency='USD', max_digits=12, decimal_places=4)),
        ))
        db.send_create_signal(u'discount', ['SelectedProduct'])

        # Adding M2M table for field products on 'SelectedProduct'
        m2m_table_name = db.shorten_name(u'discount_selectedproduct_products')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('selectedproduct', models.ForeignKey(orm[u'discount.selectedproduct'], null=False)),
            ('product', models.ForeignKey(orm[u'product.product'], null=False))
        ))
        db.create_unique(m2m_table_name, ['selectedproduct_id', 'product_id'])

        # Adding M2M table for field categories on 'SelectedProduct'
        m2m_table_name = db.shorten_name(u'discount_selectedproduct_categories')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('selectedproduct', models.ForeignKey(orm[u'discount.selectedproduct'], null=False)),
            ('category', models.ForeignKey(orm[u'product.category'], null=False))
        ))
        db.create_unique(m2m_table_name, ['selectedproduct_id', 'category_id'])


    def backwards(self, orm):
        # Deleting model 'SelectedProduct'
        db.delete_table(u'discount_selectedproduct')

        # Removing M2M table for field products on 'SelectedProduct'
        db.delete_table(db.shorten_name(u'discount_selectedproduct_products'))

        # Removing M2M table for field categories on 'SelectedProduct'
        db.delete_table(db.shorten_name(u'discount_selectedproduct_categories'))


    models = {
        u'discount.selectedproduct': {
            'Meta': {'object_name': 'SelectedProduct'},
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['product.Category']", 'symmetrical': 'False', 'blank': 'True'}),
            'discount': ('django_prices.models.PriceField', [], {'currency': "'USD'", 'max_digits': '12', 'decimal_places': '4'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'products': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['product.Product']", 'symmetrical': 'False', 'blank': 'True'})
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
        u'product.product': {
            'Meta': {'object_name': 'Product'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'products'", 'to': u"orm['product.Category']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'price': ('django_prices.models.PriceField', [], {'currency': "'USD'", 'max_digits': '12', 'decimal_places': '4'}),
            'sku': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'})
        }
    }

    complete_apps = ['discount']