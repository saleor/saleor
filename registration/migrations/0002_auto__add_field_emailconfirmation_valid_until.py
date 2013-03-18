# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'EmailConfirmation.valid_until'
        db.add_column(u'registration_emailconfirmation', 'valid_until',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 3, 21, 0, 0)),
                      keep_default=False)

    def backwards(self, orm):
        # Deleting field 'EmailConfirmation.valid_until'
        db.delete_column(u'registration_emailconfirmation', 'valid_until')

    models = {
        u'registration.emailconfirmation': {
            'Meta': {'object_name': 'EmailConfirmation'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'external_user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['registration.ExternalUserData']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'default': "'d637eaa015c5ec36ccc7f7f27fc7721e'", 'max_length': '32'}),
            'valid_until': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 3, 21, 0, 0)'})
        },
        u'registration.externaluserdata': {
            'Meta': {'unique_together': "(('provider', 'username'),)", 'object_name': 'ExternalUserData'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'provider': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'external_ids'", 'null': 'True', 'to': u"orm['userprofile.User']"}),
            'username': ('django.db.models.fields.TextField', [], {'db_index': 'True'})
        },
        u'userprofile.address': {
            'Meta': {'unique_together': "(('user', 'alias'),)", 'object_name': 'Address'},
            'alias': ('django.db.models.fields.CharField', [], {'default': "u'Home'", 'max_length': '30'}),
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
            'street_address_2': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'addressbook'", 'to': u"orm['userprofile.User']"})
        },
        u'userprofile.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_billing_address': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['userprofile.Address']"}),
            'default_shipping_address': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['userprofile.Address']"}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128'})
        }
    }

    complete_apps = ['registration']
