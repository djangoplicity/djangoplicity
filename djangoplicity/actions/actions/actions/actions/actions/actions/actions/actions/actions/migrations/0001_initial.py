# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
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
            name='ActionLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('success', models.BooleanField(default=True)),
                ('plugin', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('parameters', models.TextField(blank=True)),
                ('args', models.TextField(blank=True)),
                ('kwargs', models.TextField(blank=True)),
                ('error', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ActionParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.SlugField(max_length=255)),
                ('value', models.CharField(default=b'', max_length=255, blank=True)),
                ('type', models.CharField(default=b'str', max_length=4, choices=[(b'str', b'Text'), (b'int', b'Integer'), (b'bool', b'Boolean'), (b'date', b'Date')])),
                ('help_text', models.CharField(max_length=255, blank=True)),
                ('action', models.ForeignKey(to='actions.Action')),
            ],
            options={
                'ordering': ['action', 'name'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='actionparameter',
            unique_together=set([('action', 'name')]),
        ),
    ]
