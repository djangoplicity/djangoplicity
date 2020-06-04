# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0002_auto_20150327_1550'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='content_server',
            field=models.CharField(default=b'CDN77', max_length=255, blank=True, choices=[(b'', b'Default'), (b'media.eso.org', b'media.eso.org'), (b'CDN77', b'CDN77')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='image',
            name='content_server_ready',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
