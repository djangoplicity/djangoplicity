# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2017-08-23 14:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0021_auto_20170207_1749'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='fov_x_l',
            field=models.DecimalField(blank=True, decimal_places=5, help_text=b'Horizontal Field of View (west), in degrees', max_digits=10, null=True, verbose_name=b'FOV x West'),
        ),
        migrations.AlterField(
            model_name='image',
            name='fov_x_r',
            field=models.DecimalField(blank=True, decimal_places=5, help_text=b'Horizontal Field of View (east), in degrees', max_digits=10, null=True, verbose_name=b'FOV x East'),
        ),
        migrations.AlterField(
            model_name='image',
            name='fov_y_d',
            field=models.DecimalField(blank=True, decimal_places=5, help_text=b'Vertical Field of View (bottom), in degrees', max_digits=10, null=True, verbose_name=b'FOV y Bottom'),
        ),
        migrations.AlterField(
            model_name='image',
            name='fov_y_u',
            field=models.DecimalField(blank=True, decimal_places=5, help_text=b'Vertical Field of View (top), in degrees', max_digits=10, null=True, verbose_name=b'FOV y Top'),
        ),
    ]
