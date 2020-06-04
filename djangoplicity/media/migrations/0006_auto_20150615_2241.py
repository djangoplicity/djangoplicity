# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0003_category_enabled'),
        ('media', '0005_auto_20150611_1657'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='web_category',
            field=models.ManyToManyField(to='metadata.Category', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='video',
            name='web_category',
            field=models.ManyToManyField(to='metadata.Category', null=True, blank=True),
            preserve_default=True,
        ),
    ]
