# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Address', fields ['alias', 'user']
        db.delete_unique(u'userprofile_address', ['alias', 'user_id'])

        # Adding model 'AddressBook'
        db.create_table(u'userprofile_addressbook', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['userprofile.User'])),
            ('address', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['userprofile.Address'])),
            ('alias', self.gf('django.db.models.fields.CharField')(default=u'Home', max_length=30)),
        ))
        db.send_create_signal(u'userprofile', ['AddressBook'])

        # Adding unique constraint on 'AddressBook', fields ['user', 'alias']
        db.create_unique(u'userprofile_addressbook', ['user_id', 'alias'])

        # Deleting field 'Address.user'
        db.delete_column(u'userprofile_address', 'user_id')

        # Deleting field 'Address.alias'
        db.delete_column(u'userprofile_address', 'alias')


        # Changing field 'User.default_billing_address'
        db.alter_column(u'userprofile_user', 'default_billing_address_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['userprofile.AddressBook']))

        # Changing field 'User.default_shipping_address'
        db.alter_column(u'userprofile_user', 'default_shipping_address_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['userprofile.AddressBook']))

    def backwards(self, orm):
        # Removing unique constraint on 'AddressBook', fields ['user', 'alias']
        db.delete_unique(u'userprofile_addressbook', ['user_id', 'alias'])

        # Deleting model 'AddressBook'
        db.delete_table(u'userprofile_addressbook')

        # Adding field 'Address.user'
        db.add_column(u'userprofile_address', 'user',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, related_name='addressbook', to=orm['userprofile.User']),
                      keep_default=False)

        # Adding field 'Address.alias'
        db.add_column(u'userprofile_address', 'alias',
                      self.gf('django.db.models.fields.CharField')(default=u'Home', max_length=30),
                      keep_default=False)

        # Adding unique constraint on 'Address', fields ['alias', 'user']
        db.create_unique(u'userprofile_address', ['alias', 'user_id'])


        # Changing field 'User.default_billing_address'
        db.alter_column(u'userprofile_user', 'default_billing_address_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['userprofile.Address']))

        # Changing field 'User.default_shipping_address'
        db.alter_column(u'userprofile_user', 'default_shipping_address_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['userprofile.Address']))

    models = {
        u'userprofile.address': {
            'Meta': {'object_name': 'Address'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'company_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'country_area': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
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
            'address': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['userprofile.Address']"}),
            'alias': ('django.db.models.fields.CharField', [], {'default': "u'Home'", 'max_length': '30'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['userprofile.User']"})
        },
        u'userprofile.user': {
            'Meta': {'object_name': 'User'},
            'addresses': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['userprofile.Address']", 'through': u"orm['userprofile.AddressBook']", 'symmetrical': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_billing_address': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['userprofile.AddressBook']"}),
            'default_shipping_address': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['userprofile.AddressBook']"}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['userprofile']
