# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Uploader.data_path'
        db.alter_column(u'mydata_uploader', 'data_path', self.gf('django.db.models.fields.CharField')(max_length=256, null=True))

        # Changing field 'Uploader.user_agent_install_location'
        db.alter_column(u'mydata_uploader', 'user_agent_install_location', self.gf('django.db.models.fields.CharField')(max_length=256, null=True))

    def backwards(self, orm):

        # Changing field 'Uploader.data_path'
        db.alter_column(u'mydata_uploader', 'data_path', self.gf('django.db.models.fields.CharField')(max_length=64, null=True))

        # Changing field 'Uploader.user_agent_install_location'
        db.alter_column(u'mydata_uploader', 'user_agent_install_location', self.gf('django.db.models.fields.CharField')(max_length=128, null=True))

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
            'data_path': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
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
            'user_agent_install_location': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
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
