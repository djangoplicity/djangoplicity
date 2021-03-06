# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eventcalendar', '0002_auto_20150327_1541'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventtype',
            name='published',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='eventtype',
            name='lang',
            field=models.CharField(default=b'en', max_length=7, verbose_name='Language', db_index=True, choices=[(b'en', b'English'), (b'en-au', b'English/Australia'), (b'en-gb', b'English/United Kingdom'), (b'en-ie', b'English/Ireland'), (b'en-us', b'English/US'), (b'sq', b'Albanian'), (b'cs', b'Czech'), (b'da', b'Danish'), (b'nl', b'Dutch'), (b'nl-be', b'Dutch/Belgium'), (b'fi', b'Finnish'), (b'fr', b'French'), (b'fr-be', b'French/Belgium'), (b'fr-ch', b'French/Switzerland'), (b'de', b'German'), (b'de-at', b'German/Austria'), (b'de-be', b'German/Belgium'), (b'de-ch', b'German/Switzerland'), (b'el', b'Greek'), (b'is', b'Icelandic'), (b'it', b'Italian'), (b'it-ch', b'Italian/Switzerland'), (b'nb', b'Norwegian'), (b'pl', b'Polish'), (b'pt-br', b'Portuguese/Brazil'), (b'pt', b'Portuguese/Portugal'), (b'ru', b'Russian'), (b'es', b'Spanish'), (b'es-cl', b'Spanish/Chile'), (b'sr-latn', b'Serbian'), (b'sv', b'Swedish'), (b'tr', b'Turkish'), (b'uk', b'Ukrainian')]),
            preserve_default=True,
        ),
    ]
