# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-11-26 15:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0029_auto_20211116_1848'),
        ('metadata', '0007_auto_20151026_1529'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='logo_url',
            field=models.URLField(blank=True, max_length=255, null=True, verbose_name=b'Logo URL'),
        ),
    ]