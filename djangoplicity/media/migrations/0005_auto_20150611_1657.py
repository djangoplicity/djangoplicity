# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0004_auto_20150608_1636'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='image',
            options={'ordering': ['-priority', '-release_date'], 'permissions': [('view_only_non_default', 'Can view only non default language'), ('view_released_images_only', 'Can view only released images')]},
        ),
        migrations.AlterModelOptions(
            name='video',
            options={'ordering': ['-priority', '-release_date'], 'permissions': [('view_only_non_default', 'Can view only non default language'), ('view_released_videos_only', 'Can view only released videos')]},
        ),
    ]
