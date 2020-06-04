# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import djangoplicity.contentserver.models


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0012_auto_20151026_1529'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='content_server',
            field=djangoplicity.contentserver.models.ContentServerField(default=djangoplicity.contentserver.models._get_default_content_server, max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='video',
            name='content_server',
            field=djangoplicity.contentserver.models.ContentServerField(default=djangoplicity.contentserver.models._get_default_content_server, max_length=255, blank=True),
        ),
    ]
