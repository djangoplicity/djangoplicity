# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djangoplicity.archives.base
import djangoplicity.archives.translation
import djangoplicity.translation.fields
import djangoplicity.archives.fields


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('lang', models.CharField(default=b'en', max_length=5, verbose_name='Language', db_index=True, choices=[(b'en', b'English'), (b'en-au', b'English/Australia'), (b'en-gb', b'English/United Kingdom'), (b'en-ie', b'English/Ireland'), (b'en-us', b'English/US'), (b'sq', b'Albanian'), (b'cs', b'Czech'), (b'da', b'Danish'), (b'nl', b'Dutch'), (b'nl-be', b'Dutch/Belgium'), (b'fi', b'Finnish'), (b'fr', b'French'), (b'fr-be', b'French/Belgium'), (b'fr-ch', b'French/Switzerland'), (b'de', b'German'), (b'de-at', b'German/Austria'), (b'de-be', b'German/Belgium'), (b'de-ch', b'German/Switzerland'), (b'is', b'Icelandic'), (b'it', b'Italian'), (b'it-ch', b'Italian/Switzerland'), (b'no', b'Norwegian'), (b'pl', b'Polish'), (b'pt-br', b'Portuguese/Brazil'), (b'pt', b'Portuguese/Portugal'), (b'ru', b'Russian'), (b'es', b'Spanish'), (b'es-cl', b'Spanish/Chile'), (b'sr', b'Serbian'), (b'sv', b'Swedish'), (b'tr', b'Turkish'), (b'uk', b'Ukrainian')])),
                ('translation_ready', models.BooleanField(default=False, help_text='When you check this box and save this translation, an automatic notification email will be sent.')),
                ('id', djangoplicity.archives.fields.IdField(help_text='Ids are only allowed to contain letters, numbers, underscores or hyphens. They are used in URLs for the archive item.', serialize=False, primary_key=True)),
                ('title', djangoplicity.archives.fields.TitleField(help_text='Title is shown in browser window. Use a good informative title, since search engines normally display the title on their result pages.', max_length=200, db_index=True)),
                ('subtitle', models.CharField(help_text='Optional subtitle to be shown just above the headline.', max_length=255, blank=True)),
                ('description', djangoplicity.archives.fields.DescriptionField(help_text='', blank=True)),
                ('contacts', models.TextField(help_text='Contacts', blank=True)),
                ('links', models.TextField(help_text='Links', blank=True)),
                ('featured', models.BooleanField(default=True)),
                ('release_date', djangoplicity.archives.fields.ReleaseDateTimeField(db_index=True, null=True, blank=True)),
                ('embargo_date', djangoplicity.archives.fields.ReleaseDateTimeField(db_index=True, null=True, blank=True)),
                ('published', models.BooleanField(default=False, db_index=True, verbose_name='Published')),
                ('last_modified', models.DateTimeField(auto_now=True, verbose_name='Last modified')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
            ],
            options={
                'ordering': ['-release_date', '-id'],
                'get_latest_by': 'release_date',
                'permissions': [('view_only_non_default', 'Can view only non default language')],
            },
            bases=(djangoplicity.archives.base.ArchiveModel, models.Model),
        ),
        migrations.CreateModel(
            name='AnnouncementImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('main_visual', models.BooleanField(default=False)),
                ('override_id', models.SlugField(null=True, verbose_name='Override ID', blank=True)),
                ('hide', models.BooleanField(default=False, verbose_name='Hide on kiosk')),
                ('announcement', djangoplicity.translation.fields.TranslationForeignKey(verbose_name='Related announcement', to='announcements.Announcement', on_delete=models.deletion.CASCADE)),
                ('archive_item', djangoplicity.translation.fields.TranslationForeignKey(verbose_name='Related Image', to='media.Image', on_delete=models.deletion.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AnnouncementType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, blank=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Announcement Type',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AnnouncementVideo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('main_visual', models.BooleanField(default=False)),
                ('override_id', models.SlugField(null=True, verbose_name='Override ID', blank=True)),
                ('hide', models.BooleanField(default=False, verbose_name='Hide on kiosk')),
                ('announcement', djangoplicity.translation.fields.TranslationForeignKey(verbose_name='Related announcement', to='announcements.Announcement', on_delete=models.deletion.CASCADE)),
                ('archive_item', djangoplicity.translation.fields.TranslationForeignKey(verbose_name='Related Video', to='media.Video', on_delete=models.deletion.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WebUpdate',
            fields=[
                ('id', djangoplicity.archives.fields.IdField(help_text='Ids are only allowed to contain letters, numbers, underscores or hyphens. They are used in URLs for the archive item.', serialize=False, primary_key=True)),
                ('title', djangoplicity.archives.fields.TitleField(help_text='Title is shown in browser window. Use a good informative title, since search engines normally display the title on their result pages.', max_length=200, db_index=True)),
                ('link', djangoplicity.archives.fields.URLField(blank=True)),
                ('description', djangoplicity.archives.fields.DescriptionField(help_text='', blank=True)),
                ('release_date', djangoplicity.archives.fields.ReleaseDateTimeField(db_index=True, null=True, blank=True)),
                ('published', models.BooleanField(default=False, db_index=True, verbose_name='Published')),
                ('last_modified', models.DateTimeField(auto_now=True, verbose_name='Last modified')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
            ],
            options={
                'ordering': ['-release_date'],
            },
            bases=(djangoplicity.archives.base.ArchiveModel, models.Model),
        ),
        migrations.CreateModel(
            name='WebUpdateType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='webupdate',
            name='type',
            field=models.ForeignKey(to='announcements.WebUpdateType', on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='announcement',
            name='announcement_type',
            field=djangoplicity.translation.fields.TranslationForeignKey(default=None, blank=True, to='announcements.AnnouncementType', null=True, on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='announcement',
            name='related_images',
            field=djangoplicity.translation.fields.TranslationManyToManyField(to='media.Image', through='announcements.AnnouncementImage'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='announcement',
            name='related_videos',
            field=djangoplicity.translation.fields.TranslationManyToManyField(to='media.Video', through='announcements.AnnouncementVideo'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='announcement',
            name='source',
            field=djangoplicity.translation.fields.TranslationForeignKey(related_name='translations', verbose_name='Translation source', blank=True, to='announcements.Announcement', null=True, only_sources=False, on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='AnnouncementProxy',
            fields=[
            ],
            options={
                'verbose_name': 'Announcement translation',
                'proxy': True,
            },
            bases=('announcements.announcement', djangoplicity.archives.translation.TranslationProxyMixin),
        ),
    ]
