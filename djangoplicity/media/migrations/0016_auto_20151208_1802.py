# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0015_auto_20151208_1732'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='fov_x',
            field=models.DecimalField(decimal_places=2, max_digits=5, blank=True, help_text=b'Horizontal Field of View, in degrees', null=True, verbose_name=b'FOV x'),
        ),
        migrations.AlterField(
            model_name='image',
            name='fov_y',
            field=models.DecimalField(decimal_places=2, max_digits=5, blank=True, help_text=b'Vertical Field of View, in degrees', null=True, verbose_name=b'FOV y'),
        ),
    ]
