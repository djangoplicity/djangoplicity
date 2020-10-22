# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djangoplicity.archives.translation
import djangoplicity.translation.fields


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmbeddedPageKey',
            fields=[
                ('application', models.CharField(max_length=255)),
                ('page_key', models.SlugField(serialize=False, primary_key=True)),
                ('title', models.CharField(help_text='Meaningful title for embedded ', max_length=255)),
                ('description', models.TextField(help_text='Description of where the page is being embedded and if there is any special considerations to take - e.g. page length etc.', blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Page Embedding',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('lang', models.CharField(default=b'en', max_length=5, verbose_name='Language', db_index=True, choices=[(b'en', b'English'), (b'en-au', b'English/Australia'), (b'en-gb', b'English/United Kingdom'), (b'en-ie', b'English/Ireland'), (b'en-us', b'English/US'), (b'sq', b'Albanian'), (b'cs', b'Czech'), (b'da', b'Danish'), (b'nl', b'Dutch'), (b'nl-be', b'Dutch/Belgium'), (b'fi', b'Finnish'), (b'fr', b'French'), (b'fr-be', b'French/Belgium'), (b'fr-ch', b'French/Switzerland'), (b'de', b'German'), (b'de-at', b'German/Austria'), (b'de-be', b'German/Belgium'), (b'de-ch', b'German/Switzerland'), (b'is', b'Icelandic'), (b'it', b'Italian'), (b'it-ch', b'Italian/Switzerland'), (b'no', b'Norwegian'), (b'pl', b'Polish'), (b'pt-br', b'Portuguese/Brazil'), (b'pt', b'Portuguese/Portugal'), (b'ru', b'Russian'), (b'es', b'Spanish'), (b'es-cl', b'Spanish/Chile'), (b'sr', b'Serbian'), (b'sv', b'Swedish'), (b'tr', b'Turkish'), (b'uk', b'Ukrainian')])),
                ('translation_ready', models.BooleanField(default=False, help_text='When you check this box and save this translation, an automatic notification email will be sent.')),
                ('id', models.SlugField(help_text='ID of page', serialize=False, primary_key=True)),
                ('embedded', models.BooleanField(default=False, help_text='If checked, the page cannot be viewed through the URL. Used for pages that are embedded into complex pages like the frontpage.')),
                ('title', models.CharField(help_text='Title is shown in browser window. Use a good informative title, since search engines normally display the title on their result pages.', max_length=200)),
                ('content', models.TextField(blank=True)),
                ('script', models.TextField(help_text=b'Javascript to be included in page footer', blank=True)),
                ('description', models.TextField(help_text='The metadata description is normally shown in search engine results, making the description an effective way of capturing users attention. Description should be a clear description of the content and less the 200 characters long. Also used when sharing page on social media', blank=True)),
                ('keywords', models.TextField(help_text='Comma-separated list of keywords for this page. Mainly used internally as search engines rarely use keywords to rank pages.', blank=True)),
                ('opengraph_image', models.CharField(help_text="Example: 'http://www.eso.org/public/archives/imagecomparisons/newsfeature/potw1413a.jpg'. If given: full path to an image that will be used when sharing the page on social media. Must be larger than 200x200px and smaller than 5MB.", max_length=250, verbose_name='OpenGraph Image', blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('published', models.BooleanField(default=True, help_text='If this is unchecked, the page will not be viewable online. Timed publishing of published pages, can be controlled by the start/end publishing fields.', verbose_name='Published')),
                ('start_publishing', models.DateTimeField(help_text='Leave blank to publish immediately. The field only has effect for published pages (see above).', null=True, blank=True)),
                ('end_publishing', models.DateTimeField(help_text='Leave blank for open-ended publishing. The field only has effect for published pages (see above).', null=True, blank=True)),
                ('template_name', models.CharField(blank=True, help_text='Override the template specified by the section.', max_length=100, choices=[(b'pages/page_eson_onecolumn.html', b'Default Public one column layout'), (b'pages/blank_page.html', b'Blank page'), (b'pages/page_noborder.html', b'Public one column layout, no border')])),
                ('login_required', models.BooleanField(default=False, help_text='If checked, only logged-in users will be able to view the page.')),
                ('dynamic', models.BooleanField(default=False, help_text='If checked, page will not be cached. Use with care!')),
                ('context_processors', models.BooleanField(default=False, help_text='If checked, more variables will be available for this page.')),
                ('raw_html', models.BooleanField(default=False, help_text='If checked the WYSIWYG editor will be disabled, useful for editing pages with javascript.')),
                ('redirect_url', models.CharField(help_text="Example: 'http://www.eso.org/public/'. Used if the page has been permanently moved. If given, access to the page will trigger a HTTP 301 redirection to the given URL.", max_length=200, verbose_name='Redirect URL', db_index=True, blank=True)),
            ],
            options={
                'ordering': ['title'],
                'permissions': (('can_view_inactive', 'Can view inactive pages'),),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PageGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='Name of the group', max_length=50)),
                ('description', models.TextField(help_text='Description of group', blank=True)),
                ('full_access', models.BooleanField(default=False, help_text='If checked members of this group have access to all pages')),
                ('groups', models.ManyToManyField(help_text='Groups which have to access to this page group', to='auth.Group', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('template', models.CharField(max_length=100, choices=[(b'pages/page_eson_onecolumn.html', b'Default Public one column layout'), (b'pages/blank_page.html', b'Blank page'), (b'pages/page_noborder.html', b'Public one column layout, no border')])),
                ('append_title', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='URL',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(help_text="Example: '/about/contact/'. Make sure to have leading and trailing slashes. Good and descriptive URLs are important for good user experience and search engine ranking.", unique=True, max_length=200, verbose_name='URL', db_index=True)),
                ('page', models.ForeignKey(to='pages.Page', null=True, on_delete=models.deletion.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='page',
            name='groups',
            field=models.ManyToManyField(help_text='PageGroup the Page belongs to, used for access restriction.', to='pages.PageGroup', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='page',
            name='section',
            field=models.ForeignKey(default=1, to='pages.Section', help_text='Determines e.g. which templates to use for rendering the template.', on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='page',
            name='source',
            field=djangoplicity.translation.fields.TranslationForeignKey(related_name='translations', verbose_name='Translation source', blank=True, to='pages.Page', null=True, only_sources=False, on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='embeddedpagekey',
            name='page',
            field=models.ForeignKey(blank=True, to='pages.Page', help_text='Select page that you want to use for the specific key. Note, only pages marked as embedded pages can be selected.', null=True, on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='PageProxy',
            fields=[
            ],
            options={
                'verbose_name': 'Page translation',
                'proxy': True,
            },
            bases=('pages.page', djangoplicity.archives.translation.TranslationProxyMixin),
        ),
    ]
