# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'ExternalUserData', fields ['username', 'provider']
        db.delete_unique(u'registration_externaluserdata', ['username', 'provider'])

        # Deleting model 'EmailConfirmation'
        db.delete_table(u'registration_emailconfirmation')

        # Adding model 'EmailConfirmationRequest'
        db.create_table(u'registration_emailconfirmationrequest', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('token', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32)),
            ('valid_until', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 4, 15, 0, 0))),
        ))
        db.send_create_signal(u'registration', ['EmailConfirmationRequest'])

        # Deleting field 'ExternalUserData.provider'
        db.delete_column(u'registration_externaluserdata', 'provider')

        # Adding field 'ExternalUserData.service'
        db.add_column(u'registration_externaluserdata', 'service',
                      self.gf('django.db.models.fields.TextField')(default='', db_index=True),
                      keep_default=False)


        # Changing field 'ExternalUserData.user'
        db.alter_column(u'registration_externaluserdata', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['userprofile.User']))
        # Adding unique constraint on 'ExternalUserData', fields ['username', 'service']
        db.create_unique(u'registration_externaluserdata', ['username', 'service'])


    def backwards(self, orm):
        # Removing unique constraint on 'ExternalUserData', fields ['username', 'service']
        db.delete_unique(u'registration_externaluserdata', ['username', 'service'])

        # Adding model 'EmailConfirmation'
        db.create_table(u'registration_emailconfirmation', (
            ('valid_until', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 3, 21, 0, 0))),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('token', self.gf('django.db.models.fields.CharField')(default='d637eaa015c5ec36ccc7f7f27fc7721e', max_length=32)),
            ('external_user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['registration.ExternalUserData'], null=True, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
        ))
        db.send_create_signal(u'registration', ['EmailConfirmation'])

        # Deleting model 'EmailConfirmationRequest'
        db.delete_table(u'registration_emailconfirmationrequest')

        # Adding field 'ExternalUserData.provider'
        db.add_column(u'registration_externaluserdata', 'provider',
                      self.gf('django.db.models.fields.TextField')(default='', db_index=True),
                      keep_default=False)

        # Deleting field 'ExternalUserData.service'
        db.delete_column(u'registration_externaluserdata', 'service')


        # Changing field 'ExternalUserData.user'
        db.alter_column(u'registration_externaluserdata', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['userprofile.User']))
        # Adding unique constraint on 'ExternalUserData', fields ['username', 'provider']
        db.create_unique(u'registration_externaluserdata', ['username', 'provider'])


    models = {
        u'registration.emailconfirmationrequest': {
            'Meta': {'object_name': 'EmailConfirmationRequest'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'valid_until': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 4, 15, 0, 0)'})
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