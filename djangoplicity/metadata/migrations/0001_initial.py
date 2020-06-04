# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.SlugField(verbose_name='URL')),
                ('name', models.CharField(help_text='Title of query to be displayed to the user.', max_length=255)),
            ],
            options={
                'ordering': ('type', 'url'),
                'verbose_name_plural': 'Categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CategoryType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Facility',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('simbad_compliant', models.BooleanField(default=True)),
                ('wiki_link', models.URLField(max_length=255, blank=True)),
                ('published', models.BooleanField(default=True, verbose_name='Include in listings')),
            ],
            options={
                'ordering': ('name',),
                'verbose_name_plural': 'Facilities',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Instrument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('simbad_compliant', models.BooleanField(default=True)),
                ('wiki_link', models.URLField(max_length=255, blank=True)),
                ('published', models.BooleanField(default=True, verbose_name='Include in listings')),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ObservationProposal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('proposal_id', models.CharField(help_text='The observation proposal ID from the specific observatory.', max_length=255, verbose_name='Program/Proposal ID')),
            ],
            options={
                'ordering': ('proposal_id',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bibcode', models.CharField(help_text='ADS Bibliographic Code - see http://adsdoc.harvard.edu/abs_doc/help_pages/data.html#bibcodes', max_length=19, verbose_name='Bibliographic Code')),
            ],
            options={
                'ordering': ('-bibcode',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SubjectName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('simbad_compliant', models.BooleanField(default=True)),
                ('wiki_link', models.URLField(max_length=255, blank=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'Subject Name',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaggingStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(unique=True)),
                ('name', models.CharField(unique=True, max_length=255)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name_plural': 'tagging statuses',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaxonomyHierarchy',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('top_level', models.CharField(db_index=True, max_length=1, verbose_name='Top Level Hierarchy', choices=[(b'A', 'Solar System'), (b'B', 'Milky Way'), (b'C', 'Local Universe'), (b'D', 'Early Universe'), (b'E', 'Unspecified'), (b'X', 'Local use only')])),
                ('level1', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('level2', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('level3', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('level4', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('level5', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('name', models.CharField(unique=True, max_length=255)),
            ],
            options={
                'verbose_name_plural': 'Taxonomy Hierarchy',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='taxonomyhierarchy',
            unique_together=set([('top_level', 'level1', 'level2', 'level3', 'level4', 'level5')]),
        ),
        migrations.AddField(
            model_name='category',
            name='subject_category',
            field=models.ForeignKey(blank=True, to='metadata.TaxonomyHierarchy', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='category',
            name='subject_name',
            field=models.ForeignKey(blank=True, to='metadata.SubjectName', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='category',
            name='type',
            field=models.ForeignKey(help_text='Defines to which archive this query applies.', to='metadata.CategoryType'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='category',
            unique_together=set([('url', 'type')]),
        ),
    ]
