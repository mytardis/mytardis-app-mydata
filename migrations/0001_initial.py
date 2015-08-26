# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tardis_portal', '0003_auto_20150826_2049'),
    ]

    operations = [
        migrations.CreateModel(
            name='Uploader',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(unique=True, max_length=36)),
                ('name', models.CharField(max_length=64)),
                ('contact_name', models.CharField(max_length=64)),
                ('contact_email', models.CharField(max_length=64)),
                ('user_agent_name', models.CharField(max_length=64, null=True)),
                ('user_agent_version', models.CharField(max_length=32, null=True)),
                ('user_agent_install_location', models.CharField(max_length=256, null=True)),
                ('os_platform', models.CharField(max_length=64, null=True)),
                ('os_system', models.CharField(max_length=64, null=True)),
                ('os_release', models.CharField(max_length=32, null=True)),
                ('os_version', models.CharField(max_length=128, null=True)),
                ('os_username', models.CharField(max_length=64, null=True)),
                ('machine', models.CharField(max_length=64, null=True)),
                ('architecture', models.CharField(max_length=64, null=True)),
                ('processor', models.CharField(max_length=64, null=True)),
                ('memory', models.CharField(max_length=32, null=True)),
                ('cpus', models.IntegerField(null=True)),
                ('disk_usage', models.TextField(null=True)),
                ('data_path', models.CharField(max_length=256, null=True)),
                ('default_user', models.CharField(max_length=64, null=True)),
                ('interface', models.CharField(default=b'', max_length=64)),
                ('mac_address', models.CharField(max_length=64)),
                ('ipv4_address', models.CharField(max_length=16, null=True)),
                ('ipv6_address', models.CharField(max_length=64, null=True)),
                ('subnet_mask', models.CharField(max_length=16, null=True)),
                ('hostname', models.CharField(max_length=64, null=True)),
                ('wan_ip_address', models.CharField(max_length=64, null=True)),
                ('created_time', models.DateTimeField(null=True)),
                ('updated_time', models.DateTimeField(null=True)),
                ('instruments', models.ManyToManyField(related_name='uploaders', to='tardis_portal.Instrument', blank=True)),
            ],
            options={
                'verbose_name_plural': 'Uploaders',
            },
        ),
        migrations.CreateModel(
            name='UploaderRegistrationRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('requester_name', models.CharField(max_length=64)),
                ('requester_email', models.CharField(max_length=64)),
                ('requester_public_key', models.TextField()),
                ('requester_key_fingerprint', models.CharField(max_length=64)),
                ('request_time', models.DateTimeField(null=True, blank=True)),
                ('approved', models.BooleanField(default=False)),
                ('approver_comments', models.TextField(default=None, null=True, blank=True)),
                ('approval_expiry', models.DateField(default=None, null=True, blank=True)),
                ('approval_time', models.DateTimeField(default=None, null=True, blank=True)),
                ('approved_storage_box', models.ForeignKey(default=None, blank=True, to='tardis_portal.StorageBox', null=True)),
                ('uploader', models.ForeignKey(to='mydata.Uploader')),
            ],
            options={
                'verbose_name_plural': 'UploaderRegistrationRequests',
            },
        ),
        migrations.AlterUniqueTogether(
            name='uploaderregistrationrequest',
            unique_together=set([('uploader', 'requester_key_fingerprint')]),
        ),
    ]
