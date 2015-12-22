# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mydata', '0002_uploadersettings'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uploadersetting',
            name='value',
            field=models.TextField(blank=True),
        ),
    ]
