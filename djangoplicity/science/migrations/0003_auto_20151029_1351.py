# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import djangoplicity.translation.models
import djangoplicity.translation.fields


class Migration(migrations.Migration):

    dependencies = [
        ('science', '0002_auto_20151019_1551'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scienceannouncement',
            name='lang',
            field=djangoplicity.translation.fields.LanguageField(default=djangoplicity.translation.models._get_defaut_lang, max_length=7, verbose_name='Language', db_index=True),
        ),
    ]
