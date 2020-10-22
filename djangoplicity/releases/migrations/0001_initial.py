# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djangoplicity.archives.base
import djangoplicity.metadata.translation.fields
import djangoplicity.translation.fields
import djangoplicity.archives.fields


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0001_initial'),
        ('media', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('isocode', models.CharField(max_length=2, serialize=False, verbose_name='ISO Code', primary_key=True)),
                ('url_prefix', models.CharField(max_length=255, verbose_name='URL Prefix')),
                ('name', models.CharField(max_length=255)),
                ('flag_url', models.CharField(max_length=255, verbose_name='Flag URL')),
            ],
            options={
                'ordering': ('name',),
                'verbose_name_plural': 'countries',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Release',
            fields=[
                ('lang', models.CharField(default=b'en', max_length=5, verbose_name='Language', db_index=True, choices=[(b'en', b'English'), (b'en-au', b'English/Australia'), (b'en-gb', b'English/United Kingdom'), (b'en-ie', b'English/Ireland'), (b'en-us', b'English/US'), (b'sq', b'Albanian'), (b'cs', b'Czech'), (b'da', b'Danish'), (b'nl', b'Dutch'), (b'nl-be', b'Dutch/Belgium'), (b'fi', b'Finnish'), (b'fr', b'French'), (b'fr-be', b'French/Belgium'), (b'fr-ch', b'French/Switzerland'), (b'de', b'German'), (b'de-at', b'German/Austria'), (b'de-be', b'German/Belgium'), (b'de-ch', b'German/Switzerland'), (b'is', b'Icelandic'), (b'it', b'Italian'), (b'it-ch', b'Italian/Switzerland'), (b'no', b'Norwegian'), (b'pl', b'Polish'), (b'pt-br', b'Portuguese/Brazil'), (b'pt', b'Portuguese/Portugal'), (b'ru', b'Russian'), (b'es', b'Spanish'), (b'es-cl', b'Spanish/Chile'), (b'sr', b'Serbian'), (b'sv', b'Swedish'), (b'tr', b'Turkish'), (b'uk', b'Ukrainian')])),
                ('translation_ready', models.BooleanField(default=False, help_text='When you check this box and save this translation, an automatic notification email will be sent.')),
                ('id', models.SlugField(help_text='Id of release - e.g. heic0801. The id must be unique.', serialize=False, primary_key=True)),
                ('old_ids', models.CharField(help_text='For backwards compatibility: Historic ids of this press release.', max_length=50, verbose_name='Old Ids', blank=True)),
                ('title', models.CharField(help_text='Title is shown in browser window. Use a good informative title, since search engines normally display the title on their result pages.', max_length=255, db_index=True)),
                ('subtitle', models.CharField(help_text='Optional subtitle to be shown just above the headline.', max_length=255, blank=True)),
                ('release_city', models.CharField(help_text='The city of the release - e.g. Paris. Can be left blank.', max_length=100, blank=True)),
                ('headline', models.TextField(help_text='HTML code in lead is not allowed. The lead is further more normally shown in search engine results, making the description an effective way of capturing users attention.', blank=True)),
                ('description', models.TextField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('more_information', models.TextField(blank=True)),
                ('links', models.TextField(help_text='Help text', blank=True)),
                ('disclaimer', models.TextField(help_text='Disclaimer for press release - usually e.g. retractions of previously issued press releases.', blank=True)),
                ('meltwater_keywords', models.TextField(help_text='Used to store Meltwater Keywords.', verbose_name='Keywords', blank=True)),
                ('kids_title', models.CharField(max_length=255, blank=True)),
                ('kids_description', models.TextField(blank=True)),
                ('release_date', djangoplicity.archives.fields.ReleaseDateTimeField(db_index=True, null=True, blank=True)),
                ('embargo_date', djangoplicity.archives.fields.ReleaseDateTimeField(db_index=True, null=True, blank=True)),
                ('published', models.BooleanField(default=False, db_index=True, verbose_name='Published')),
                ('last_modified', models.DateTimeField(auto_now=True, verbose_name='Last modified')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('facility', djangoplicity.metadata.translation.fields.TranslationFacilityManyToManyField(help_text='Telescopes or observatories used for the observations.', to='metadata.Facility', null=True, verbose_name='Facility', blank=True)),
                ('kids_image', models.ForeignKey(related_name='kids_image_release_set', blank=True, to='media.Image', help_text='Use this to override the default Release image.', null=True, on_delete=models.deletion.CASCADE)),
                ('publications', djangoplicity.metadata.translation.fields.TranslationAVMPublicationField(help_text='ADS Bibliographic Code', to='metadata.Publication', null=True, verbose_name='Publication', blank=True)),
                ('subject_category', djangoplicity.metadata.translation.fields.TranslationAVMSubjectCategoryField(help_text='The type(s) of object or objects in the resource, or general subject matter of an image, taken from a controlled vocabulary taxonomy.', to='metadata.TaxonomyHierarchy', null=True, verbose_name='Subject Category', blank=True)),
                ('subject_name', djangoplicity.metadata.translation.fields.TranslationAVMSubjectNameField(help_text='Proper names/catalog numbers for key objects/subjects in the image field.', to='metadata.SubjectName', null=True, verbose_name='Subject Name', blank=True)),
            ],
            options={
                'ordering': ['-release_date', '-id'],
                'get_latest_by': 'release_date',
                'verbose_name': 'Press Release',
                'verbose_name_plural': 'Press Releases',
                'permissions': [('view_only_non_default', 'Can view only non default language')],
            },
            bases=(djangoplicity.archives.base.ArchiveModel, models.Model),
        ),
        migrations.CreateModel(
            name='ReleaseContact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, blank=True)),
                ('email', models.CharField(max_length=255, blank=True)),
                ('telephone', models.CharField(max_length=255, blank=True)),
                ('cellular', models.CharField(max_length=255, blank=True)),
                ('affiliation', models.CharField(max_length=255, blank=True)),
                ('address', models.CharField(max_length=255, blank=True)),
                ('city', models.CharField(max_length=255, blank=True)),
                ('state_province', models.CharField(max_length=255, blank=True)),
                ('postal_code', models.CharField(max_length=255, blank=True)),
                ('country', models.CharField(max_length=255, blank=True)),
                ('release', djangoplicity.translation.fields.TranslationForeignKey(to='releases.Release', on_delete=models.deletion.CASCADE)),
            ],
            options={
                'ordering': ('id',),
                'verbose_name': 'contact',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReleaseImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('main_visual', models.BooleanField(default=False)),
                ('override_id', models.SlugField(null=True, verbose_name='Override ID', blank=True)),
                ('hide', models.BooleanField(default=False, verbose_name='Hide on kiosk')),
                ('zoomable', models.BooleanField(default=False, verbose_name='Zoomable if main')),
                ('archive_item', djangoplicity.translation.fields.TranslationForeignKey(verbose_name='Related Image', to='media.Image', on_delete=models.deletion.CASCADE)),
                ('release', djangoplicity.translation.fields.TranslationForeignKey(verbose_name='Related release', to='releases.Release', on_delete=models.deletion.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReleaseImageComparison',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('main_visual', models.BooleanField(default=False)),
                ('override_id', models.SlugField(null=True, verbose_name='Override ID', blank=True)),
                ('hide', models.BooleanField(default=False, verbose_name='Hide on kiosk')),
                ('archive_item', djangoplicity.translation.fields.TranslationForeignKey(verbose_name='Related Image Comparison', to='media.ImageComparison', on_delete=models.deletion.CASCADE)),
                ('release', djangoplicity.translation.fields.TranslationForeignKey(verbose_name='Related release', to='releases.Release', on_delete=models.deletion.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReleaseStockImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('main_visual', models.BooleanField(default=False)),
                ('override_id', models.SlugField(null=True, verbose_name='Override ID', blank=True)),
                ('hide', models.BooleanField(default=False, verbose_name='Hide on kiosk')),
                ('archive_item', djangoplicity.translation.fields.TranslationForeignKey(verbose_name='Related Stock Image', to='media.Image', on_delete=models.deletion.CASCADE)),
                ('release', djangoplicity.translation.fields.TranslationForeignKey(verbose_name='Related release', to='releases.Release', on_delete=models.deletion.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReleaseTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url_suffix', models.CharField(max_length=255, verbose_name='URL Suffix')),
                ('country', models.ForeignKey(to='releases.Country', on_delete=models.deletion.CASCADE)),
                ('release', models.ForeignKey(to='releases.Release', on_delete=models.deletion.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReleaseTranslationContact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, blank=True)),
                ('email', models.CharField(max_length=255, blank=True)),
                ('telephone', models.CharField(max_length=255, blank=True)),
                ('cellular', models.CharField(max_length=255, blank=True)),
                ('affiliation', models.CharField(max_length=255, blank=True)),
                ('address', models.CharField(max_length=255, blank=True)),
                ('city', models.CharField(max_length=255, blank=True)),
                ('state_province', models.CharField(max_length=255, blank=True)),
                ('postal_code', models.CharField(max_length=255, blank=True)),
                ('country', models.CharField(max_length=255, blank=True)),
                ('release', djangoplicity.translation.fields.TranslationForeignKey(to='releases.Release', only_sources=False, on_delete=models.deletion.CASCADE)),
            ],
            options={
                'verbose_name': 'translation contact',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReleaseType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, blank=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Press Release Type',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReleaseVideo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('main_visual', models.BooleanField(default=False)),
                ('override_id', models.SlugField(null=True, verbose_name='Override ID', blank=True)),
                ('hide', models.BooleanField(default=False, verbose_name='Hide on kiosk')),
                ('archive_item', djangoplicity.translation.fields.TranslationForeignKey(verbose_name='Related Video', to='media.Video', on_delete=models.deletion.CASCADE)),
                ('release', djangoplicity.translation.fields.TranslationForeignKey(verbose_name='Related release', to='releases.Release', on_delete=models.deletion.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='release',
            name='related_comparisons',
            field=djangoplicity.translation.fields.TranslationManyToManyField(to='media.ImageComparison', through='releases.ReleaseImageComparison'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='release',
            name='related_images',
            field=djangoplicity.translation.fields.TranslationManyToManyField(to='media.Image', through='releases.ReleaseImage'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='release',
            name='related_videos',
            field=djangoplicity.translation.fields.TranslationManyToManyField(to='media.Video', through='releases.ReleaseVideo'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='release',
            name='release_type',
            field=djangoplicity.translation.fields.TranslationForeignKey(default=1, to='releases.ReleaseType', on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='release',
            name='source',
            field=djangoplicity.translation.fields.TranslationForeignKey(related_name='translations', verbose_name='Translation source', blank=True, to='releases.Release', null=True, only_sources=False, on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='release',
            name='stock_images',
            field=djangoplicity.translation.fields.TranslationManyToManyField(related_name='stock', through='releases.ReleaseStockImage', to='media.Image'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='KidsRelease',
            fields=[
            ],
            options={
                'verbose_name': 'Kids Press Release',
                'proxy': True,
            },
            bases=('releases.release',),
        ),
        migrations.CreateModel(
            name='ReleaseProxy',
            fields=[
            ],
            options={
                'verbose_name': 'Press Release Translation',
                'proxy': True,
            },
            bases=('releases.release',),
        ),
    ]
