# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2019-10-29 15:28
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0008_merge_20191007_1425'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='page',
            options={'ordering': ['title'], 'permissions': (('can_view_inactive', 'Can view inactive pages'), ('view_elt_pages_only', 'Can view only ELT pages'))},
        ),
    ]
