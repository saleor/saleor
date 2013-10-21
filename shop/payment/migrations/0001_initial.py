# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Payment'
        db.create_table(u'payment_payment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('variant', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('status', self.gf('django.db.models.fields.CharField')(default='waiting', max_length=10)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('transaction_id', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('currency', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('total', self.gf('django.db.models.fields.DecimalField')(default='0.0', max_digits=9, decimal_places=2)),
            ('delivery', self.gf('django.db.models.fields.DecimalField')(default='0.0', max_digits=9, decimal_places=2)),
            ('tax', self.gf('django.db.models.fields.DecimalField')(default='0.0', max_digits=9, decimal_places=2)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('country_area', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('zip', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('extra_data', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('token', self.gf('django.db.models.fields.CharField')(default='', max_length=36, blank=True)),
            ('success_url', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('cancel_url', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['order.Order'])),
        ))
        db.send_create_signal(u'payment', ['Payment'])


    def backwards(self, orm):
        # Deleting model 'Payment'
        db.delete_table(u'payment_payment')


    models = {
        u'order.order': {
            'Meta': {'ordering': "('-last_status_change',)", 'object_name': 'Order'},
            'billing_address': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['userprofile.Address']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_status_change': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'payment_status': ('django.db.models.fields.CharField', [], {'default': "'initial'", 'max_length': '32'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '32'}),
            'token': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '36', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['userprofile.User']"})
        },
        u'payment.payment': {
            'Meta': {'object_name': 'Payment'},
            'cancel_url': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'country_area': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'currency': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'delivery': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'max_digits': '9', 'decimal_places': '2'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'extra_data': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['order.Order']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'waiting'", 'max_length': '10'}),
            'success_url': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'tax': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'max_digits': '9', 'decimal_places': '2'}),
            'token': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '36', 'blank': 'True'}),
            'total': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'max_digits': '9', 'decimal_places': '2'}),
            'transaction_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'variant': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'})
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

    complete_apps = ['payment']