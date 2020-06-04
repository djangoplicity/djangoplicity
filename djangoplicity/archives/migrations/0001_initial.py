# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        UnaccentExtension()
    ]
