# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('science', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='scienceannouncement',
            name='embargo_task_id',
            field=models.CharField(max_length=64, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='scienceannouncement',
            name='release_task_id',
            field=models.CharField(max_length=64, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='scienceannouncement',
            name='lang',
            field=models.CharField(default=b'en', max_length=7, verbose_name='Language', db_index=True, choices=[(b'en', b'English')]),
            preserve_default=True,
        ),
    ]
