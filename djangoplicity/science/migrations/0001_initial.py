# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djangoplicity.archives.fields
import djangoplicity.archives.base
import djangoplicity.translation.fields


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScienceAnnouncement',
            fields=[
                ('lang', models.CharField(default=b'en', max_length=5, verbose_name='Language', db_index=True, choices=[(b'en', b'English')])),
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
            name='ScienceAnnouncementImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('main_visual', models.BooleanField(default=False)),
                ('override_id', models.SlugField(null=True, verbose_name='Override ID', blank=True)),
                ('hide', models.BooleanField(default=False, verbose_name='Hide on kiosk')),
                ('archive_item', models.ForeignKey(verbose_name='Related Image', to='media.Image')),
                ('science_announcement', models.ForeignKey(verbose_name='Related science announcement', to='science.ScienceAnnouncement')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='scienceannouncement',
            name='related_images',
            field=models.ManyToManyField(to='media.Image', through='science.ScienceAnnouncementImage'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='scienceannouncement',
            name='source',
            field=djangoplicity.translation.fields.TranslationForeignKey(related_name='translations', verbose_name='Translation source', blank=True, to='science.ScienceAnnouncement', null=True, only_sources=False),
            preserve_default=True,
        ),
    ]
