# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djangoplicity.translation.models
import djangoplicity.metadata.translation.fields
import djangoplicity.translation.fields


class Migration(migrations.Migration):

    dependencies = [
        ('releases', '0003_auto_20151009_1400'),
    ]

    operations = [
        migrations.AlterField(
            model_name='release',
            name='facility',
            field=djangoplicity.metadata.translation.fields.TranslationFacilityManyToManyField(help_text='Telescopes or observatories used for the observations.', to='metadata.Facility', verbose_name='Facility', blank=True),
        ),
        migrations.AlterField(
            model_name='release',
            name='lang',
            field=djangoplicity.translation.fields.LanguageField(default=djangoplicity.translation.models._get_defaut_lang, max_length=7, verbose_name='Language', db_index=True),
        ),
        migrations.AlterField(
            model_name='release',
            name='publications',
            field=djangoplicity.metadata.translation.fields.TranslationAVMPublicationField(help_text='ADS Bibliographic Code', to='metadata.Publication', verbose_name='Publication', blank=True),
        ),
        migrations.AlterField(
            model_name='release',
            name='subject_category',
            field=djangoplicity.metadata.translation.fields.TranslationAVMSubjectCategoryField(help_text='The type(s) of object or objects in the resource, or general subject matter of an image, taken from a controlled vocabulary taxonomy.', to='metadata.TaxonomyHierarchy', verbose_name='Subject Category', blank=True),
        ),
        migrations.AlterField(
            model_name='release',
            name='subject_name',
            field=djangoplicity.metadata.translation.fields.TranslationAVMSubjectNameField(help_text='Proper names/catalog numbers for key objects/subjects in the image field.', to='metadata.SubjectName', verbose_name='Subject Name', blank=True),
        ),
    ]
