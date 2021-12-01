# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.contrib.sites.models import Site



def move_category(apps, schema_editor):
    # Category = apps.get_model('metadata', 'Category')
    # I need to import the model directly, even though the doc does not condone it
    from djangoplicity.metadata.models import Category  

    setnames = {
        'Images': 'image_set',
        'Videos': 'video_set',
    } 

    for x in Category.objects.all():
        if x.subject_category:
            for image in getattr(x.subject_category, setnames[x.type.name]).all():
                if not x.subject_name or x.subject_name in image.subject_name.all():
                    image.web_category.add(x)
                    # TODO web categories: on migration 0006: remove old links if image.subject_category.top_level == 'X'
        elif x.subject_name:
            for image in getattr(x.subject_name, setnames[x.type.name]).all():
                image.web_category.add(x)

class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0004_fix_metadata_category_names'),
        ('metadata', '0008_category_logo'),
    ]

    operations = [
        migrations.RunPython(move_category),
    ]
