# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djangoplicity.translation.models
import djangoplicity.pages.models
import djangoplicity.translation.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0002_auto_20150327_1541'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='groups',
            field=models.ManyToManyField(help_text='PageGroup the Page belongs to, used for access restriction.', to='pages.PageGroup', blank=True),
        ),
        migrations.AlterField(
            model_name='page',
            name='lang',
            field=djangoplicity.translation.fields.LanguageField(default=djangoplicity.translation.models._get_defaut_lang, max_length=7, verbose_name='Language', db_index=True),
        ),
        migrations.AlterField(
            model_name='page',
            name='template_name',
            field=models.CharField(blank=True, help_text='Override the template specified by the section.', max_length=100, choices=[(b'pages/page_onecolumn.html', b'Default one column layout'), (b'pages/page_twocolumn.html', b'Default two column layout'), (b'pages/page_noborder.html', b'One column layout, no border')]),
        ),
        migrations.AlterField(
            model_name='pagegroup',
            name='groups',
            field=models.ManyToManyField(help_text='Groups which have to access to this page group', to='auth.Group', blank=True),
        ),
        migrations.AlterField(
            model_name='section',
            name='template',
            field=djangoplicity.pages.models.TemplateField(max_length=100),
        ),
    ]
