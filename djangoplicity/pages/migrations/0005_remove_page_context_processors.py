# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-08 13:29
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0004_auto_20151028_1120'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='page',
            name='context_processors',
        ),
    ]
