# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def set_featured_images(apps, schema_editor):
    '''
    If any image is marked as "hidden" in any release or announcement we
    set it to featured=False
    '''
    Image = apps.get_model('media', 'Image')
    ReleaseImage = apps.get_model('releases', 'ReleaseImage')
    AnnouncementImage = apps.get_model('announcements', 'AnnouncementImage')

    for i in Image.objects.all():
        featured = list(ReleaseImage.objects.filter(archive_item=i).values_list('hide', flat=True))
        featured += list(AnnouncementImage.objects.filter(archive_item=i).values_list('hide', flat=True))
        featured = any(featured)
        if featured:
            Image.objects.filter(pk=i.pk).update(featured=False)


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0013_auto_20151104_1428'),
        ('releases', '0004_auto_20151026_1529'),
        ('announcements', '0004_auto_20151026_1529'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='featured',
            field=models.BooleanField(default=True, verbose_name='Featured on Kiosk, etc.'),
        ),
        migrations.AddField(
            model_name='imagecomparison',
            name='featured',
            field=models.BooleanField(default=True, verbose_name='Featured on Kiosk, etc.'),
        ),
        migrations.AddField(
            model_name='video',
            name='featured',
            field=models.BooleanField(default=False, verbose_name='Featured on Kiosk, etc.'),
        ),
        migrations.RunPython(set_featured_images, migrations.RunPython.noop)
    ]
