# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0002_auto_20150417_1939'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='enabled',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
