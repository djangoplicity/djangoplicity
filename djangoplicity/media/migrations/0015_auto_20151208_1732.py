# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0014_auto_20151110_1500'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='fov_x',
            field=models.DecimalField(decimal_places=2, max_digits=3, blank=True, help_text=b'Horizontal Field of View, in degrees', null=True, verbose_name=b'FOV x'),
        ),
        migrations.AddField(
            model_name='image',
            name='fov_y',
            field=models.DecimalField(decimal_places=2, max_digits=3, blank=True, help_text=b'Vertical Field of View, in degrees', null=True, verbose_name=b'FOV y'),
        ),
        migrations.AlterField(
            model_name='image',
            name='featured',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='imagecomparison',
            name='featured',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='video',
            name='featured',
            field=models.BooleanField(default=False),
        ),
    ]
