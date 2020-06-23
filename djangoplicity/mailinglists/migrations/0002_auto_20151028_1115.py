# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mailinglists', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bademailaddress',
            name='email',
            field=models.EmailField(unique=True, max_length=254),
        ),
        migrations.AlterField(
            model_name='subscriber',
            name='email',
            field=models.EmailField(unique=True, max_length=254),
        ),
    ]
