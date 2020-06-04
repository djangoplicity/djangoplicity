# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djangoplicity.metadata.translation.fields
import djangoplicity.contentserver.models
import djangoplicity.translation.fields
import djangoplicity.translation.models


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0011_auto_20151009_1400'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='content_server',
            field=djangoplicity.contentserver.models.ContentServerField(default=djangoplicity.contentserver.models._get_content_server_choices, max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='image',
            name='lang',
            field=djangoplicity.translation.fields.LanguageField(default=djangoplicity.translation.models._get_defaut_lang, max_length=7, verbose_name='Language', db_index=True),
        ),
        migrations.AlterField(
            model_name='image',
            name='subject_category',
            field=djangoplicity.metadata.translation.fields.TranslationAVMSubjectCategoryField(help_text='The type(s) of object or objects in the resource, or general subject matter of an image, taken from a controlled vocabulary taxonomy.', to='metadata.TaxonomyHierarchy', verbose_name='Subject Category', blank=True),
        ),
        migrations.AlterField(
            model_name='image',
            name='subject_name',
            field=djangoplicity.metadata.translation.fields.TranslationAVMSubjectNameField(help_text='Proper names/catalog numbers for key objects/subjects in the image field.', to='metadata.SubjectName', verbose_name='Subject Name', blank=True),
        ),
        migrations.AlterField(
            model_name='image',
            name='web_category',
            field=models.ManyToManyField(to='metadata.Category', blank=True),
        ),
        migrations.AlterField(
            model_name='imagecomparison',
            name='lang',
            field=djangoplicity.translation.fields.LanguageField(default=djangoplicity.translation.models._get_defaut_lang, max_length=7, verbose_name='Language', db_index=True),
        ),
        migrations.AlterField(
            model_name='pictureoftheweek',
            name='lang',
            field=djangoplicity.translation.fields.LanguageField(default=djangoplicity.translation.models._get_defaut_lang, max_length=7, verbose_name='Language', db_index=True),
        ),
        migrations.AlterField(
            model_name='video',
            name='content_server',
            field=djangoplicity.contentserver.models.ContentServerField(default=djangoplicity.contentserver.models._get_content_server_choices, max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='video',
            name='facility',
            field=djangoplicity.metadata.translation.fields.TranslationFacilityManyToManyField(help_text='Telescopes or observatories used for the observations.', to='metadata.Facility', verbose_name='Facility', blank=True),
        ),
        migrations.AlterField(
            model_name='video',
            name='lang',
            field=djangoplicity.translation.fields.LanguageField(default=djangoplicity.translation.models._get_defaut_lang, max_length=7, verbose_name='Language', db_index=True),
        ),
        migrations.AlterField(
            model_name='video',
            name='subject_category',
            field=djangoplicity.metadata.translation.fields.TranslationAVMSubjectCategoryField(help_text='The type(s) of object or objects in the resource, or general subject matter of an image, taken from a controlled vocabulary taxonomy.', to='metadata.TaxonomyHierarchy', verbose_name='Subject Category', blank=True),
        ),
        migrations.AlterField(
            model_name='video',
            name='subject_name',
            field=djangoplicity.metadata.translation.fields.TranslationAVMSubjectNameField(help_text='Proper names/catalog numbers for key objects/subjects in the image field.', to='metadata.SubjectName', verbose_name='Subject Name', blank=True),
        ),
        migrations.AlterField(
            model_name='video',
            name='use_youtube',
            field=models.BooleanField(default=False, verbose_name='Use YouTube player'),
        ),
        migrations.AlterField(
            model_name='video',
            name='web_category',
            field=models.ManyToManyField(to='metadata.Category', blank=True),
        ),
        migrations.AlterField(
            model_name='video',
            name='youtube_video_id',
            field=models.CharField(max_length=11, null=True, verbose_name='YouTube VideoID', blank=True),
        ),
        migrations.AlterField(
            model_name='videobroadcastaudiotrack',
            name='type',
            field=models.CharField(max_length=25, verbose_name='Audio track type', choices=[(b'stereo', b'Stereo soundtrack'), (b'split_stereo', b'Split stereo'), (b'surround', b'Surround 5.1'), (b'split_surround', b'Split surround 5.1')]),
        ),
    ]
