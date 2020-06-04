# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djangoplicity.archives.fields
import djangoplicity.metadata.archives.fields
import djangoplicity.archives.base


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0001_initial'),
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Donation',
            fields=[
                ('sale', models.BooleanField(default=False, help_text='For sale - note weight must be provided if product is for sale.')),
                ('price', models.DecimalField(default=b'0.00', help_text='Price (EUR)', max_digits=8, decimal_places=2)),
                ('job', models.CharField(help_text=djangoplicity.archives.contrib.satchmo.models.DEFAULT_JOB_NO_HELP_TEXT_FUNC, max_length=4, blank=True)),
                ('jsp', models.IntegerField(help_text=djangoplicity.archives.contrib.satchmo.models.DEFAULT_JSP_NO_FUNC, null=True, verbose_name='JSP', blank=True)),
                ('account_no', models.CharField(help_text=djangoplicity.archives.contrib.satchmo.models.DEFAULT_ACCOUNT_NO_FUNC, max_length=10, blank=True)),
                ('free', models.BooleanField(default=False, help_text='Available for free.', verbose_name=b'Free')),
                ('shippable', models.BooleanField(default=True, help_text='Calculate shipping for this item.')),
                ('id', djangoplicity.archives.fields.IdField(help_text='Ids are only allowed to contain letters, numbers, underscores or hyphens. They are used in URLs for the archive item.', serialize=False, primary_key=True)),
                ('title', djangoplicity.archives.fields.TitleField(help_text='Title is shown in browser window. Use a good informative title, since search engines normally display the title on their result pages.', max_length=200, db_index=True)),
                ('description', djangoplicity.archives.fields.DescriptionField(help_text='', blank=True)),
                ('priority', djangoplicity.archives.fields.PriorityField(default=0, help_text='Priority of product (100 highest, 0 lowest) - high priority products are ranked higher in search results than low priority products.', db_index=True)),
                ('credit', djangoplicity.metadata.archives.fields.AVMCreditField(default=djangoplicity.products.base.consts.DEFAULT_CREDIT_FUNC, help_text='The minimum information that the Publisher would like to see mentioned when the resource is used.', null=False, blank=True)),
                ('release_date', djangoplicity.archives.fields.ReleaseDateTimeField(db_index=True, null=True, blank=True)),
                ('embargo_date', djangoplicity.archives.fields.ReleaseDateTimeField(db_index=True, null=True, blank=True)),
                ('published', models.BooleanField(default=False, db_index=True, verbose_name='Published')),
                ('last_modified', models.DateTimeField(auto_now=True, verbose_name='Last modified')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('product', models.OneToOneField(null=True, blank=True, to='product.Product')),
            ],
            options={
                'ordering': ['-priority', '-id'],
                'abstract': False,
            },
            bases=(djangoplicity.archives.base.ArchiveModel, models.Model),
        ),
    ]
