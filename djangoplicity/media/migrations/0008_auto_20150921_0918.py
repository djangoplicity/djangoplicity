# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0007_auto_20150630_1224'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='distance_ly_is_accurate',
            field=models.BooleanField(default=False, verbose_name='Distance in ly is accurate'),
            preserve_default=True,
        ),
    ]
