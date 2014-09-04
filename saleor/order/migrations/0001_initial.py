# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Order'
        db.create_table(u'order_order', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default=u'new', max_length=32)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('last_status_change', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name=u'orders', null=True, to=orm['userprofile.User'])),
            ('tracking_client_id', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('billing_address', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'+', to=orm['userprofile.Address'])),
            ('anonymous_user_email', self.gf('django.db.models.fields.EmailField')(default=u'', max_length=75, blank=True)),
            ('token', self.gf('django.db.models.fields.CharField')(default=u'', max_length=36, blank=True)),
        ))
        db.send_create_signal(u'order', ['Order'])

        # Adding model 'DeliveryGroup'
        db.create_table(u'order_deliverygroup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default=u'new', max_length=32)),
            ('method', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'groups', to=orm['order.Order'])),
            ('price', self.gf('django_prices.models.PriceField')(default=0, currency='AED', max_digits=12, decimal_places=4)),
        ))
        db.send_create_signal(u'order', ['DeliveryGroup'])

        # Adding model 'ShippedDeliveryGroup'
        db.create_table(u'order_shippeddeliverygroup', (
            (u'deliverygroup_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['order.DeliveryGroup'], unique=True, primary_key=True)),
            ('address', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'+', to=orm['userprofile.Address'])),
        ))
        db.send_create_signal(u'order', ['ShippedDeliveryGroup'])

        # Adding model 'DigitalDeliveryGroup'
        db.create_table(u'order_digitaldeliverygroup', (
            (u'deliverygroup_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['order.DeliveryGroup'], unique=True, primary_key=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
        ))
        db.send_create_signal(u'order', ['DigitalDeliveryGroup'])

        # Adding model 'OrderedItem'
        db.create_table(u'order_ordereditem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('delivery_group', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'items', to=orm['order.DeliveryGroup'])),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name=u'+', null=True, on_delete=models.SET_NULL, to=orm['product.Product'])),
            ('product_name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('product_sku', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('quantity', self.gf('django.db.models.fields.IntegerField')()),
            ('unit_price_net', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=4)),
            ('unit_price_gross', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=4)),
        ))
        db.send_create_signal(u'order', ['OrderedItem'])

        # Adding model 'Payment'
        db.create_table(u'order_payment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('variant', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('status', self.gf('django.db.models.fields.CharField')(default=u'waiting', max_length=10)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('transaction_id', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('currency', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('total', self.gf('django.db.models.fields.DecimalField')(default=u'0.0', max_digits=9, decimal_places=2)),
            ('delivery', self.gf('django.db.models.fields.DecimalField')(default=u'0.0', max_digits=9, decimal_places=2)),
            ('tax', self.gf('django.db.models.fields.DecimalField')(default=u'0.0', max_digits=9, decimal_places=2)),
            ('description', self.gf('django.db.models.fields.TextField')(default=u'', blank=True)),
            ('billing_first_name', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('billing_last_name', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('billing_address_1', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('billing_address_2', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('billing_city', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('billing_postcode', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('billing_country_code', self.gf('django.db.models.fields.CharField')(max_length=2, blank=True)),
            ('billing_country_area', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('extra_data', self.gf('django.db.models.fields.TextField')(default=u'', blank=True)),
            ('token', self.gf('django.db.models.fields.CharField')(default=u'', max_length=36, blank=True)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'payments', to=orm['order.Order'])),
        ))
        db.send_create_signal(u'order', ['Payment'])


    def backwards(self, orm):
        # Deleting model 'Order'
        db.delete_table(u'order_order')

        # Deleting model 'DeliveryGroup'
        db.delete_table(u'order_deliverygroup')

        # Deleting model 'ShippedDeliveryGroup'
        db.delete_table(u'order_shippeddeliverygroup')

        # Deleting model 'DigitalDeliveryGroup'
        db.delete_table(u'order_digitaldeliverygroup')

        # Deleting model 'OrderedItem'
        db.delete_table(u'order_ordereditem')

        # Deleting model 'Payment'
        db.delete_table(u'order_payment')


    models = {
        u'order.deliverygroup': {
            'Meta': {'object_name': 'DeliveryGroup'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'groups'", 'to': u"orm['order.Order']"}),
            'price': ('django_prices.models.PriceField', [], {'default': '0', 'currency': "'AED'", 'max_digits': '12', 'decimal_places': '4'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "u'new'", 'max_length': '32'})
        },
        u'order.digitaldeliverygroup': {
            'Meta': {'object_name': 'DigitalDeliveryGroup', '_ormbases': [u'order.DeliveryGroup']},
            u'deliverygroup_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['order.DeliveryGroup']", 'unique': 'True', 'primary_key': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'})
        },
        u'order.order': {
            'Meta': {'ordering': "(u'-last_status_change',)", 'object_name': 'Order'},
            'anonymous_user_email': ('django.db.models.fields.EmailField', [], {'default': "u''", 'max_length': '75', 'blank': 'True'}),
            'billing_address': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'+'", 'to': u"orm['userprofile.Address']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_status_change': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "u'new'", 'max_length': '32'}),
            'token': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '36', 'blank': 'True'}),
            'tracking_client_id': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'orders'", 'null': 'True', 'to': u"orm['userprofile.User']"})
        },
        u'order.ordereditem': {
            'Meta': {'object_name': 'OrderedItem'},
            'delivery_group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'items'", 'to': u"orm['order.DeliveryGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['product.Product']"}),
            'product_name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'product_sku': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'quantity': ('django.db.models.fields.IntegerField', [], {}),
            'unit_price_gross': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '4'}),
            'unit_price_net': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '4'})
        },
        u'order.payment': {
            'Meta': {'object_name': 'Payment'},
            'billing_address_1': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'billing_address_2': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'billing_city': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'billing_country_area': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'billing_country_code': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'}),
            'billing_first_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'billing_last_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'billing_postcode': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'currency': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'delivery': ('django.db.models.fields.DecimalField', [], {'default': "u'0.0'", 'max_digits': '9', 'decimal_places': '2'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            'extra_data': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'payments'", 'to': u"orm['order.Order']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "u'waiting'", 'max_length': '10'}),
            'tax': ('django.db.models.fields.DecimalField', [], {'default': "u'0.0'", 'max_digits': '9', 'decimal_places': '2'}),
            'token': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '36', 'blank': 'True'}),
            'total': ('django.db.models.fields.DecimalField', [], {'default': "u'0.0'", 'max_digits': '9', 'decimal_places': '2'}),
            'transaction_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'variant': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'order.shippeddeliverygroup': {
            'Meta': {'object_name': 'ShippedDeliveryGroup', '_ormbases': [u'order.DeliveryGroup']},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'+'", 'to': u"orm['userprofile.Address']"}),
            u'deliverygroup_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['order.DeliveryGroup']", 'unique': 'True', 'primary_key': 'True'})
        },
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
        u'userprofile.address': {
            'Meta': {'object_name': 'Address'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'street_address': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        u'userprofile.addressbook': {
            'Meta': {'unique_together': "((u'user', u'alias'),)", 'object_name': 'AddressBook'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'+'", 'unique': 'True', 'to': u"orm['userprofile.Address']"}),
            'alias': ('django.db.models.fields.CharField', [], {'default': "u'Home'", 'max_length': '30'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'address_book'", 'to': u"orm['userprofile.User']"})
        },
        u'userprofile.user': {
            'Meta': {'object_name': 'User'},
            'addresses': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['userprofile.Address']", 'through': u"orm['userprofile.AddressBook']", 'symmetrical': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_billing_address': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['userprofile.AddressBook']"}),
            'default_shipping_address': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['userprofile.AddressBook']"}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['order']