# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djangoplicity.translation.models
import djangoplicity.translation.fields


class Migration(migrations.Migration):

    dependencies = [
        ('newsletters', '0003_auto_20151009_1400'),
    ]

    operations = [
        migrations.AlterField(
            model_name='language',
            name='lang',
            field=djangoplicity.translation.fields.LanguageField(max_length=7, serialize=False, verbose_name='Language', primary_key=True),
        ),
        migrations.AlterField(
            model_name='mailchimpcampaign',
            name='lang',
            field=djangoplicity.translation.fields.LanguageField(default=b'', max_length=7, choices=[(b'en', b'English')]),
        ),
        migrations.AlterField(
            model_name='newsletter',
            name='from_email',
            field=models.EmailField(max_length=254, blank=True),
        ),
        migrations.AlterField(
            model_name='newsletter',
            name='lang',
            field=djangoplicity.translation.fields.LanguageField(default=djangoplicity.translation.models._get_defaut_lang, max_length=7, verbose_name='Language', db_index=True),
        ),
        migrations.AlterField(
            model_name='newsletterlanguage',
            name='default_from_email',
            field=models.EmailField(max_length=254, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='newslettertype',
            name='default_from_email',
            field=models.EmailField(max_length=254),
        ),
    ]
