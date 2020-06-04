# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('releases', '0004_auto_20151026_1529'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='releasetranslationcontact',
            options={'ordering': ('id',), 'verbose_name': 'translation contact'},
        ),
    ]
