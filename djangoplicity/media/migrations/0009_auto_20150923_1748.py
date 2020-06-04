# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0008_auto_20150921_0918'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='use_youtube',
            field=models.BooleanField(default=False, help_text='Use YouTube player'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='video',
            name='youtube_video_id',
            field=models.CharField(help_text='YouTube Video ID', max_length=11, null=True, blank=True),
            preserve_default=True,
        ),
    ]
