# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djangoplicity.archives.base
import djangoplicity.newsletters.models
import djangoplicity.translation.fields
import djangoplicity.archives.fields
import djangoplicity.archives.translation


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataSourceOrdering',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('fields', models.SlugField()),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DataSourceSelector',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('filter', models.CharField(default=b'I', max_length=1, choices=[(b'I', b'Include'), (b'E', b'Exclude')])),
                ('field', models.SlugField()),
                ('match', models.SlugField()),
                ('value', models.CharField(max_length=255)),
                ('type', models.CharField(default=b'str', max_length=4, choices=[(b'str', b'Text'), (b'int', b'Integer'), (b'bool', b'Boolean'), (b'date', b'Date')])),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('lang', models.CharField(max_length=5, serialize=False, verbose_name='Language', primary_key=True, choices=[(b'en', b'English'), (b'en-au', b'English/Australia'), (b'en-gb', b'English/United Kingdom'), (b'en-ie', b'English/Ireland'), (b'en-us', b'English/US'), (b'sq', b'Albanian'), (b'cs', b'Czech'), (b'da', b'Danish'), (b'nl', b'Dutch'), (b'nl-be', b'Dutch/Belgium'), (b'fi', b'Finnish'), (b'fr', b'French'), (b'fr-be', b'French/Belgium'), (b'fr-ch', b'French/Switzerland'), (b'de', b'German'), (b'de-at', b'German/Austria'), (b'de-be', b'German/Belgium'), (b'de-ch', b'German/Switzerland'), (b'is', b'Icelandic'), (b'it', b'Italian'), (b'it-ch', b'Italian/Switzerland'), (b'no', b'Norwegian'), (b'pl', b'Polish'), (b'pt-br', b'Portuguese/Brazil'), (b'pt', b'Portuguese/Portugal'), (b'ru', b'Russian'), (b'es', b'Spanish'), (b'es-cl', b'Spanish/Chile'), (b'sr', b'Serbian'), (b'sv', b'Swedish'), (b'tr', b'Turkish'), (b'uk', b'Ukrainian')])),
            ],
            options={
                'ordering': ['lang'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailChimpCampaign',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('list_id', models.CharField(max_length=50)),
                ('campaign_id', models.CharField(max_length=50)),
                ('lang', models.CharField(default=b'', max_length=5, choices=[(b'en', b'English'), (b'en-au', b'English/Australia'), (b'en-gb', b'English/United Kingdom'), (b'en-ie', b'English/Ireland'), (b'en-us', b'English/US'), (b'sq', b'Albanian'), (b'cs', b'Czech'), (b'da', b'Danish'), (b'nl', b'Dutch'), (b'nl-be', b'Dutch/Belgium'), (b'fi', b'Finnish'), (b'fr', b'French'), (b'fr-be', b'French/Belgium'), (b'fr-ch', b'French/Switzerland'), (b'de', b'German'), (b'de-at', b'German/Austria'), (b'de-be', b'German/Belgium'), (b'de-ch', b'German/Switzerland'), (b'is', b'Icelandic'), (b'it', b'Italian'), (b'it-ch', b'Italian/Switzerland'), (b'no', b'Norwegian'), (b'pl', b'Polish'), (b'pt-br', b'Portuguese/Brazil'), (b'pt', b'Portuguese/Portugal'), (b'ru', b'Russian'), (b'es', b'Spanish'), (b'es-cl', b'Spanish/Chile'), (b'sr', b'Serbian'), (b'sv', b'Swedish'), (b'tr', b'Turkish'), (b'uk', b'Ukrainian')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Mailer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('plugin', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailerLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('success', models.BooleanField(default=True)),
                ('is_test', models.BooleanField(default=False)),
                ('plugin', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('parameters', models.TextField(blank=True)),
                ('subject', models.CharField(max_length=255)),
                ('newsletter_pk', models.IntegerField()),
                ('error', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailerParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.SlugField(max_length=255)),
                ('value', models.CharField(default=b'', max_length=255, blank=True)),
                ('type', models.CharField(default=b'str', max_length=4, choices=[(b'str', b'Text'), (b'int', b'Integer'), (b'bool', b'Boolean'), (b'date', b'Date')])),
                ('help_text', models.CharField(max_length=255, blank=True)),
                ('mailer', models.ForeignKey(to='newsletters.Mailer')),
            ],
            options={
                'ordering': ['mailer', 'name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Newsletter',
            fields=[
                ('lang', models.CharField(default=b'en', max_length=5, verbose_name='Language', db_index=True, choices=[(b'en', b'English'), (b'en-au', b'English/Australia'), (b'en-gb', b'English/United Kingdom'), (b'en-ie', b'English/Ireland'), (b'en-us', b'English/US'), (b'sq', b'Albanian'), (b'cs', b'Czech'), (b'da', b'Danish'), (b'nl', b'Dutch'), (b'nl-be', b'Dutch/Belgium'), (b'fi', b'Finnish'), (b'fr', b'French'), (b'fr-be', b'French/Belgium'), (b'fr-ch', b'French/Switzerland'), (b'de', b'German'), (b'de-at', b'German/Austria'), (b'de-be', b'German/Belgium'), (b'de-ch', b'German/Switzerland'), (b'is', b'Icelandic'), (b'it', b'Italian'), (b'it-ch', b'Italian/Switzerland'), (b'no', b'Norwegian'), (b'pl', b'Polish'), (b'pt-br', b'Portuguese/Brazil'), (b'pt', b'Portuguese/Portugal'), (b'ru', b'Russian'), (b'es', b'Spanish'), (b'es-cl', b'Spanish/Chile'), (b'sr', b'Serbian'), (b'sv', b'Swedish'), (b'tr', b'Turkish'), (b'uk', b'Ukrainian')])),
                ('translation_ready', models.BooleanField(default=False, help_text='When you check this box and save this translation, an automatic notification email will be sent.')),
                ('id', models.SlugField(serialize=False, primary_key=True)),
                ('frozen', models.BooleanField(default=False)),
                ('scheduled_status', models.CharField(default=b'OFF', max_length=10, choices=[(b'OFF', b'Not Scheduled'), (b'ONGOING', b'Being Scheduled'), (b'ON', b'Scheduled')])),
                ('scheduled_task_id', models.CharField(max_length=64, blank=True)),
                ('send', models.DateTimeField(null=True, verbose_name=b'Sent', blank=True)),
                ('start_date', models.DateTimeField(null=True, blank=True)),
                ('end_date', models.DateTimeField(null=True, blank=True)),
                ('from_name', models.CharField(max_length=255, blank=True)),
                ('from_email', models.EmailField(max_length=75, blank=True)),
                ('subject', models.CharField(max_length=255, blank=True)),
                ('text', models.TextField(blank=True)),
                ('html', models.TextField(verbose_name=b'HTML', blank=True)),
                ('editorial_subject', models.CharField(max_length=255, blank=True)),
                ('editorial', models.TextField(blank=True)),
                ('editorial_text', models.TextField(blank=True)),
                ('release_date', djangoplicity.archives.fields.ReleaseDateTimeField(db_index=True, null=True, blank=True)),
                ('published', models.BooleanField(default=False, db_index=True, verbose_name='Published')),
                ('last_modified', models.DateTimeField(auto_now=True, verbose_name='Last modified')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('source', djangoplicity.translation.fields.TranslationForeignKey(related_name='translations', verbose_name='Translation source', blank=True, to='newsletters.Newsletter', null=True, only_sources=False)),
            ],
            options={
                'ordering': ['-release_date'],
            },
            bases=(djangoplicity.archives.base.ArchiveModel, models.Model),
        ),
        migrations.CreateModel(
            name='NewsletterContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.SlugField()),
            ],
            options={
                'ordering': ['newsletter', 'data_source', 'object_id'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NewsletterDataSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('list', models.BooleanField(default=True)),
                ('name', models.SlugField(help_text='Name used to access this data source in templates')),
                ('title', models.CharField(max_length=255)),
                ('limit', models.CharField(max_length=255, blank=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('ordering', models.ForeignKey(blank=True, to='newsletters.DataSourceOrdering', null=True)),
                ('selectors', models.ManyToManyField(to='newsletters.DataSourceSelector', blank=True)),
            ],
            options={
                'ordering': ['type__name', 'title'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NewsletterLanguage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('default_from_name', models.CharField(max_length=255, null=True, blank=True)),
                ('default_from_email', models.EmailField(max_length=75, null=True, blank=True)),
                ('default_editorial', models.TextField(blank=True)),
                ('default_editorial_text', models.TextField(blank=True)),
                ('language', models.ForeignKey(to='newsletters.Language')),
            ],
            options={
                'ordering': ['language'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NewsletterType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(help_text='Slug for e.g. online archive URL')),
                ('default_from_name', models.CharField(max_length=255)),
                ('default_from_email', models.EmailField(max_length=75)),
                ('subject_template', models.CharField(max_length=255, blank=True)),
                ('text_template', models.TextField(blank=True)),
                ('html_template', models.TextField(verbose_name=b'HTML template', blank=True)),
                ('archive', models.BooleanField(default=True, help_text='Enable public archives for this newsletter type.')),
                ('local_archive', models.BooleanField(default=False, help_text='Use local archive (instead of e.g. Mailchimp Online archive)')),
                ('internal_archive', models.BooleanField(default=False, help_text='Restrict archive to internal network only.')),
                ('sharing', models.BooleanField(default=True, help_text='Enable social sharing of newsletter.')),
                ('subscribe_text', models.TextField(help_text='Instructions and link to subscribe to the newsletter', blank=True)),
                ('languages', models.ManyToManyField(to='newsletters.Language', through='newsletters.NewsletterLanguage', blank=True)),
                ('mailers', models.ManyToManyField(to='newsletters.Mailer', blank=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='newsletterlanguage',
            name='newsletter_type',
            field=models.ForeignKey(to='newsletters.NewsletterType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='newsletterdatasource',
            name='type',
            field=models.ForeignKey(to='newsletters.NewsletterType'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='newsletterdatasource',
            unique_together=set([('type', 'name')]),
        ),
        migrations.AddField(
            model_name='newslettercontent',
            name='data_source',
            field=models.ForeignKey(blank=True, to='newsletters.NewsletterDataSource', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='newslettercontent',
            name='newsletter',
            field=models.ForeignKey(to='newsletters.Newsletter'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='newsletter',
            name='type',
            field=models.ForeignKey(to='newsletters.NewsletterType'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='mailerparameter',
            unique_together=set([('mailer', 'name')]),
        ),
        migrations.AddField(
            model_name='mailchimpcampaign',
            name='newsletter',
            field=models.ForeignKey(to='newsletters.Newsletter'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='mailchimpcampaign',
            unique_together=set([('newsletter', 'list_id', 'lang')]),
        ),
        migrations.CreateModel(
            name='NewsletterProxy',
            fields=[
            ],
            options={
                'ordering': ['lang'],
                'verbose_name': 'Newsletter translation',
                'proxy': True,
            },
            bases=('newsletters.newsletter', djangoplicity.archives.translation.TranslationProxyMixin),
        ),
    ]
