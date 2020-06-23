# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('newsletters', '0002_auto_20150327_1546'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsletter',
            name='embargo_task_id',
            field=models.CharField(max_length=64, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='newsletter',
            name='release_task_id',
            field=models.CharField(max_length=64, null=True, blank=True),
            preserve_default=True,
        ),
    ]
