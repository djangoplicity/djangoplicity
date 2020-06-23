# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actions', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BadEmailAddress',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(unique=True, max_length=75)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ('email',),
                'verbose_name_plural': 'bad email addresses',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GroupMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('field', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='List',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('base_url', models.CharField(max_length=255)),
                ('name', models.SlugField(unique=True)),
                ('password', models.SlugField()),
                ('last_sync', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailChimpEventAction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('on_event', models.CharField(max_length=50, db_index=True)),
                ('action', models.ForeignKey(to='actions.Action')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailChimpGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group_id', models.IntegerField(db_index=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailChimpGrouping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group_id', models.IntegerField(db_index=True)),
                ('name', models.CharField(max_length=255)),
                ('option', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['name', 'option'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailChimpList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('api_key', models.CharField(default=b'', max_length=255, verbose_name=b'API key')),
                ('list_id', models.CharField(unique=True, max_length=50)),
                ('synchronize', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=255, blank=True)),
                ('web_id', models.CharField(max_length=255, blank=True)),
                ('email_type_option', models.CharField(max_length=50, blank=True)),
                ('use_awesomebar', models.BooleanField(default=False)),
                ('default_from_name', models.CharField(max_length=255, blank=True)),
                ('default_from_email', models.CharField(max_length=255, blank=True)),
                ('default_subject', models.CharField(max_length=255, blank=True)),
                ('default_language', models.CharField(max_length=10, blank=True)),
                ('list_rating', models.IntegerField(null=True, blank=True)),
                ('member_count', models.IntegerField(null=True, blank=True)),
                ('unsubscribe_count', models.IntegerField(null=True, blank=True)),
                ('cleaned_count', models.IntegerField(null=True, blank=True)),
                ('member_count_since_send', models.IntegerField(null=True, blank=True)),
                ('unsubscribe_count_since_send', models.IntegerField(null=True, blank=True)),
                ('cleaned_count_since_send', models.IntegerField(null=True, blank=True)),
                ('avg_sub_rate', models.IntegerField(help_text=b'per month', null=True, blank=True)),
                ('avg_unsub_rate', models.IntegerField(help_text=b'per month', null=True, blank=True)),
                ('target_sub_rate', models.IntegerField(help_text=b'per month', null=True, blank=True)),
                ('open_rate', models.IntegerField(help_text=b'per campaign', null=True, blank=True)),
                ('click_rate', models.IntegerField(help_text=b'per campaign', null=True, blank=True)),
                ('connected', models.BooleanField(default=False)),
                ('last_sync', models.DateTimeField(null=True, blank=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', help_text=b'Select the content type of objects that subscribers on this list can be linked with.', null=True)),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailChimpListToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(unique=True, max_length=36, verbose_name=b'UUID')),
                ('token', models.CharField(unique=True, max_length=56)),
                ('expired', models.DateTimeField(null=True, blank=True)),
                ('list', models.ForeignKey(to='mailinglists.MailChimpList')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailChimpMergeVar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('required', models.BooleanField(default=False)),
                ('field_type', models.CharField(blank=True, max_length=20, choices=[(b'email', b'email'), (b'text', b'text'), (b'number', b'number'), (b'radio', b'radio'), (b'dropdown', b'dropdown'), (b'date', b'date'), (b'address', b'address'), (b'phone', b'phone'), (b'url', b'url'), (b'imageurl', b'imageurl')])),
                ('public', models.BooleanField(default=False)),
                ('show', models.BooleanField(default=False)),
                ('order', models.CharField(max_length=255, blank=True)),
                ('default', models.CharField(max_length=255, blank=True)),
                ('size', models.CharField(max_length=255, blank=True)),
                ('tag', models.CharField(max_length=255, blank=True)),
                ('choices', models.TextField(blank=True)),
                ('list', models.ForeignKey(to='mailinglists.MailChimpList')),
            ],
            options={
                'ordering': ['list', 'name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MergeVarMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('field', models.CharField(max_length=255)),
                ('list', models.ForeignKey(to='mailinglists.MailChimpList')),
                ('merge_var', models.ForeignKey(to='mailinglists.MailChimpMergeVar')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Subscriber',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(unique=True, max_length=75)),
            ],
            options={
                'ordering': ('email',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('list', models.ForeignKey(to='mailinglists.List')),
                ('subscriber', models.ForeignKey(to='mailinglists.Subscriber')),
            ],
            options={
                'ordering': ('subscriber__email',),
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='subscription',
            unique_together=set([('subscriber', 'list')]),
        ),
        migrations.AddField(
            model_name='mailchimplist',
            name='primary_key_field',
            field=models.ForeignKey(blank=True, to='mailinglists.MailChimpMergeVar', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mailchimpgrouping',
            name='list',
            field=models.ForeignKey(to='mailinglists.MailChimpList'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mailchimpgroup',
            name='list',
            field=models.ForeignKey(to='mailinglists.MailChimpList'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mailchimpeventaction',
            name='model_object',
            field=models.ForeignKey(to='mailinglists.MailChimpList'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='list',
            name='subscribers',
            field=models.ManyToManyField(to='mailinglists.Subscriber', through='mailinglists.Subscription', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='groupmapping',
            name='group',
            field=models.ForeignKey(to='mailinglists.MailChimpGroup'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='groupmapping',
            name='list',
            field=models.ForeignKey(to='mailinglists.MailChimpList'),
            preserve_default=True,
        ),
    ]
