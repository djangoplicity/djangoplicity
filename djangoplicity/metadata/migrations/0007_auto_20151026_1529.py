# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0006_auto_20150618_1827'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxonomyhierarchy',
            name='top_level',
            field=models.CharField(db_index=True, max_length=1, verbose_name='Top Level Hierarchy', choices=[(b'A', 'Solar System'), (b'B', 'Milky Way'), (b'C', 'Local Universe'), (b'D', 'Early Universe'), (b'E', 'Unspecified')]),
        ),
    ]
