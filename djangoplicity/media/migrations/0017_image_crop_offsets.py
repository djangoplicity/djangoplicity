# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0016_auto_20151208_1802'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='crop_offsets',
            field=models.TextField(null=True, blank=True),
        ),
    ]
