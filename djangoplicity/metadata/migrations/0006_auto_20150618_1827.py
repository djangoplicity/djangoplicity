# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0005_move_metadata_category'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ('type', 'name'), 'verbose_name': 'Web Category', 'verbose_name_plural': 'Web Categories'},
        ),
        migrations.RemoveField(
            model_name='category',
            name='subject_category',
        ),
        migrations.RemoveField(
            model_name='category',
            name='subject_name',
        ),
    ]
