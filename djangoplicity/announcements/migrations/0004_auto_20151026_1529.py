# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djangoplicity.translation.models
import djangoplicity.translation.fields


class Migration(migrations.Migration):

    dependencies = [
        ('announcements', '0003_auto_20151009_1400'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='lang',
            field=djangoplicity.translation.fields.LanguageField(default=djangoplicity.translation.models._get_defaut_lang, max_length=7, verbose_name='Language', db_index=True),
        ),
    ]
