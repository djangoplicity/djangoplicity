# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_donation'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='periodical',
            name='product',
        ),
        migrations.DeleteModel(
            name='Periodical',
        ),
    ]
