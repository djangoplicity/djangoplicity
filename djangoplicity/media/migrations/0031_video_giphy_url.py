# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2021-05-14 04:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0030_auto_20220329_1612'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='giphy_url',
            field=models.URLField(blank=True, max_length=255),
        ),
    ]
