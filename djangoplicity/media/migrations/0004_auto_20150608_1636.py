# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0003_auto_20150424_1602'),
    ]

    operations = [
        migrations.AddField(
            model_name='videobroadcastaudiotrack',
            name='type',
            field=models.CharField(default='split_stereo', max_length=25, verbose_name='Split audio type', choices=[(b'stereo', b'Stereo soundtrack'), (b'split_stereo', b'Split stereo'), (b'surround', b'Surround 5.1'), (b'split_surround', b'Split surround 5.1')]),
            preserve_default=False,
        ),
    ]
