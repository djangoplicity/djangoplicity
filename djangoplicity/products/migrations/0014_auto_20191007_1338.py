# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2019-10-07 13:38
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0013_auto_20190926_1509'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='archivecategory',
            options={'verbose_name': 'Archive Category', 'verbose_name_plural': 'Archive Categories'},
        ),
    ]