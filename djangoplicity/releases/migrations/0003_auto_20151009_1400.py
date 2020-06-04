# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('releases', '0002_auto_20150327_1541'),
    ]

    operations = [
        migrations.AddField(
            model_name='release',
            name='embargo_task_id',
            field=models.CharField(max_length=64, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='release',
            name='release_task_id',
            field=models.CharField(max_length=64, null=True, blank=True),
            preserve_default=True,
        ),
    ]
