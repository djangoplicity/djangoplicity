# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import djangoplicity.translation.fields


class Migration(migrations.Migration):

    dependencies = [
        ('newsletters', '0004_auto_20151028_1103'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mailchimpcampaign',
            name='lang',
            field=djangoplicity.translation.fields.LanguageField(default=b'', max_length=7),
        ),
    ]
