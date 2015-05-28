# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Uploader'
        db.create_table(u'mydata_uploader', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=36)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('contact_name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('contact_email', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('user_agent_name', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('user_agent_version', self.gf('django.db.models.fields.CharField')(max_length=32, null=True)),
            ('user_agent_install_location', self.gf('django.db.models.fields.CharField')(max_length=128, null=True)),
            ('os_platform', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('os_system', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('os_release', self.gf('django.db.models.fields.CharField')(max_length=32, null=True)),
            ('os_version', self.gf('django.db.models.fields.CharField')(max_length=128, null=True)),
            ('os_username', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('machine', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('architecture', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('processor', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('memory', self.gf('django.db.models.fields.CharField')(max_length=32, null=True)),
            ('cpus', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('disk_usage', self.gf('django.db.models.fields.TextField')(null=True)),
            ('data_path', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('default_user', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('interface', self.gf('django.db.models.fields.CharField')(default='', max_length=64)),
            ('mac_address', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('ipv4_address', self.gf('django.db.models.fields.CharField')(max_length=16, null=True)),
            ('ipv6_address', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('subnet_mask', self.gf('django.db.models.fields.CharField')(max_length=16, null=True)),
            ('hostname', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('wan_ip_address', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('created_time', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('updated_time', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal('mydata', ['Uploader'])

        # Adding M2M table for field instruments on 'Uploader'
        m2m_table_name = db.shorten_name(u'mydata_uploader_instruments')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('uploader', models.ForeignKey(orm['mydata.uploader'], null=False)),
            ('instrument', models.ForeignKey(orm['tardis_portal.instrument'], null=False))
        ))
        db.create_unique(m2m_table_name, ['uploader_id', 'instrument_id'])

        # Adding model 'UploaderRegistrationRequest'
        db.create_table(u'mydata_uploaderregistrationrequest', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uploader', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mydata.Uploader'])),
            ('requester_name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('requester_email', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('requester_public_key', self.gf('django.db.models.fields.TextField')()),
            ('requester_key_fingerprint', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('request_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('approved', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('approved_storage_box', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['tardis_portal.StorageBox'], null=True, blank=True)),
            ('approver_comments', self.gf('django.db.models.fields.TextField')(default=None, null=True, blank=True)),
            ('approval_expiry', self.gf('django.db.models.fields.DateField')(default=None, null=True, blank=True)),
            ('approval_time', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal('mydata', ['UploaderRegistrationRequest'])

        # Adding unique constraint on 'UploaderRegistrationRequest', fields ['uploader', 'requester_key_fingerprint']
        db.create_unique(u'mydata_uploaderregistrationrequest', ['uploader_id', 'requester_key_fingerprint'])


    def backwards(self, orm):
        # Removing unique constraint on 'UploaderRegistrationRequest', fields ['uploader', 'requester_key_fingerprint']
        db.delete_unique(u'mydata_uploaderregistrationrequest', ['uploader_id', 'requester_key_fingerprint'])

        # Deleting model 'Uploader'
        db.delete_table(u'mydata_uploader')

        # Removing M2M table for field instruments on 'Uploader'
        db.delete_table(db.shorten_name(u'mydata_uploader_instruments'))

        # Deleting model 'UploaderRegistrationRequest'
        db.delete_table(u'mydata_uploaderregistrationrequest')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'mydata.uploader': {
            'Meta': {'object_name': 'Uploader'},
            'architecture': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'contact_email': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'contact_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'cpus': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'created_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'data_path': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'default_user': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'disk_usage': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instruments': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'uploaders'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['tardis_portal.Instrument']"}),
            'interface': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '64'}),
            'ipv4_address': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True'}),
            'ipv6_address': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'mac_address': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'machine': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'memory': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'os_platform': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'os_release': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            'os_system': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'os_username': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'os_version': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'processor': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'subnet_mask': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True'}),
            'updated_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'user_agent_install_location': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'user_agent_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'user_agent_version': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36'}),
            'wan_ip_address': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'})
        },
        'mydata.uploaderregistrationrequest': {
            'Meta': {'unique_together': "(['uploader', 'requester_key_fingerprint'],)", 'object_name': 'UploaderRegistrationRequest'},
            'approval_expiry': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'approval_time': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'approved_storage_box': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['tardis_portal.StorageBox']", 'null': 'True', 'blank': 'True'}),
            'approver_comments': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'request_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'requester_email': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'requester_key_fingerprint': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'requester_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'requester_public_key': ('django.db.models.fields.TextField', [], {}),
            'uploader': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mydata.Uploader']"})
        },
        'tardis_portal.facility': {
            'Meta': {'object_name': 'Facility'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manager_group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'tardis_portal.instrument': {
            'Meta': {'object_name': 'Instrument'},
            'facility': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Facility']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'tardis_portal.storagebox': {
            'Meta': {'object_name': 'StorageBox'},
            'description': ('django.db.models.fields.TextField', [], {'default': "'Default Storage'"}),
            'django_storage_class': ('django.db.models.fields.TextField', [], {'default': "'tardis.tardis_portal.storage.MyTardisLocalFileSystemStorage'"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'master_box': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'child_boxes'", 'null': 'True', 'to': "orm['tardis_portal.StorageBox']"}),
            'max_size': ('django.db.models.fields.BigIntegerField', [], {}),
            'name': ('django.db.models.fields.TextField', [], {'default': "'default'", 'unique': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['mydata']