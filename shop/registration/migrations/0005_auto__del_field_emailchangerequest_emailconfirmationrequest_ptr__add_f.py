# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'EmailChangeRequest.emailconfirmationrequest_ptr'
        db.delete_column(u'registration_emailchangerequest', u'emailconfirmationrequest_ptr_id')

        # Adding field 'EmailChangeRequest.id'
        db.add_column(u'registration_emailchangerequest', u'id',
                      self.gf('django.db.models.fields.AutoField')(default=0, primary_key=True),
                      keep_default=False)

        # Adding field 'EmailChangeRequest.token'
        db.add_column(u'registration_emailchangerequest', 'token',
                      self.gf('django.db.models.fields.CharField')(default=0, unique=True, max_length=32),
                      keep_default=False)

        # Adding field 'EmailChangeRequest.valid_until'
        db.add_column(u'registration_emailchangerequest', 'valid_until',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 4, 27, 0, 0)),
                      keep_default=False)

        # Adding field 'EmailChangeRequest.email'
        db.add_column(u'registration_emailchangerequest', 'email',
                      self.gf('django.db.models.fields.EmailField')(default=0, max_length=75),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'EmailChangeRequest.emailconfirmationrequest_ptr'
        db.add_column(u'registration_emailchangerequest', u'emailconfirmationrequest_ptr',
                      self.gf('django.db.models.fields.related.OneToOneField')(default=0, to=orm['registration.EmailConfirmationRequest'], unique=True, primary_key=True),
                      keep_default=False)

        # Deleting field 'EmailChangeRequest.id'
        db.delete_column(u'registration_emailchangerequest', u'id')

        # Deleting field 'EmailChangeRequest.token'
        db.delete_column(u'registration_emailchangerequest', 'token')

        # Deleting field 'EmailChangeRequest.valid_until'
        db.delete_column(u'registration_emailchangerequest', 'valid_until')

        # Deleting field 'EmailChangeRequest.email'
        db.delete_column(u'registration_emailchangerequest', 'email')


    models = {
        u'registration.emailchangerequest': {
            'Meta': {'object_name': 'EmailChangeRequest'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'email_change_requests'", 'to': u"orm['userprofile.User']"}),
            'valid_until': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 4, 27, 0, 0)'})
        },
        u'registration.emailconfirmationrequest': {
            'Meta': {'object_name': 'EmailConfirmationRequest'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'valid_until': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 4, 27, 0, 0)'})
        },
        u'registration.externaluserdata': {
            'Meta': {'unique_together': "[['service', 'username']]", 'object_name': 'ExternalUserData'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'service': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'external_ids'", 'to': u"orm['userprofile.User']"}),
            'username': ('django.db.models.fields.TextField', [], {'db_index': 'True'})
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

    complete_apps = ['registration']