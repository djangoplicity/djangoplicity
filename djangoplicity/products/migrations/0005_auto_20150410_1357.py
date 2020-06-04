# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_auto_20150308_2056'),
    ]

    operations = [
        migrations.DeleteModel(
            name='SlideShow',
        ),
    ]
