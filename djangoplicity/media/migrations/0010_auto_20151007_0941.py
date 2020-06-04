# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0009_auto_20150923_1748'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='n_pixels',
            field=models.BigIntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.RunSQL('UPDATE media_image SET n_pixels = width * height'),
    ]
