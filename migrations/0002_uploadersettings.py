# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mydata', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UploaderSetting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.TextField()),
                ('value', models.TextField()),
            ],
            options={
                'verbose_name': 'UploaderSetting',
                'verbose_name_plural': 'UploaderSettings',
            },
        ),
        migrations.AddField(
            model_name='uploader',
            name='settings_downloaded',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='uploader',
            name='settings_updated',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='uploadersetting',
            name='uploader',
            field=models.ForeignKey(related_name='settings', to='mydata.Uploader'),
        ),
    ]
