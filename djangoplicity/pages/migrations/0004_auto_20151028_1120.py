# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djangoplicity.pages.models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0003_auto_20151026_1529'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='template_name',
            field=djangoplicity.pages.models.TemplateField(help_text='Override the template specified by the section.', max_length=100, blank=True),
        ),
    ]
