# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Order.payment_status'
        db.delete_column(u'order_order', 'payment_status')


    def backwards(self, orm):
        # Adding field 'Order.payment_status'
        db.add_column(u'order_order', 'payment_status',
                      self.gf('django.db.models.fields.CharField')(default='initial', max_length=32),
                      keep_default=False)


    models = {
        u'order.deliverygroup': {
            'Meta': {'object_name': 'DeliveryGroup'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groups'", 'to': u"orm['order.Order']"}),
            'price': ('django_prices.models.PriceField', [], {'default': '0', 'currency': "'USD'", 'max_digits': '12', 'decimal_places': '4'})
        },
        u'order.digitaldeliverygroup': {
            'Meta': {'object_name': 'DigitalDeliveryGroup', '_ormbases': [u'order.DeliveryGroup']},
            u'deliverygroup_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['order.DeliveryGroup']", 'unique': 'True', 'primary_key': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'})
        },
        u'order.order': {
            'Meta': {'ordering': "('-last_status_change',)", 'object_name': 'Order'},
            'billing_address': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['userprofile.Address']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_status_change': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '32'}),
            'token': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '36', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['userprofile.User']"})
        },
        u'order.ordereditem': {
            'Meta': {'object_name': 'OrderedItem'},
            'delivery_group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': u"orm['order.DeliveryGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['product.Product']"}),
            'product_name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'quantity': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '4'}),
            'unit_price_gross': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '4'}),
            'unit_price_net': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '4'})
        },
        u'order.shippeddeliverygroup': {
            'Meta': {'object_name': 'ShippedDeliveryGroup', '_ormbases': [u'order.DeliveryGroup']},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['userprofile.Address']"}),
            u'deliverygroup_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['order.DeliveryGroup']", 'unique': 'True', 'primary_key': 'True'})
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
            'price': ('django_prices.models.PriceField', [], {'currency': "'USD'", 'max_digits': '12', 'decimal_places': '4'})
        },
        u'userprofile.address': {
            'Meta': {'object_name': 'Address'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'company_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'country_area': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'street_address_1': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'street_address_2': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'})
        },
        u'userprofile.addressbook': {
            'Meta': {'unique_together': "(('user', 'alias'),)", 'object_name': 'AddressBook'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'unique': 'True', 'to': u"orm['userprofile.Address']"}),
            'alias': ('django.db.models.fields.CharField', [], {'default': "u'Home'", 'max_length': '30'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'address_book'", 'to': u"orm['userprofile.User']"})
        },
        u'userprofile.user': {
            'Meta': {'object_name': 'User'},
            'addresses': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['userprofile.Address']", 'through': u"orm['userprofile.AddressBook']", 'symmetrical': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_billing_address': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['userprofile.AddressBook']"}),
            'default_shipping_address': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['userprofile.AddressBook']"}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['order']