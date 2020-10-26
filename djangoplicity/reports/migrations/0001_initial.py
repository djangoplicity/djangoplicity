# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('is_mailable', models.BooleanField(default=False)),
                ('description', models.CharField(max_length=255, null=True, blank=True)),
                ('displayed_fields', models.TextField(help_text='Please write the fields to be displayed in a semi-colon seprated format')),
                ('sql_command', models.TextField(verbose_name='SQL Command')),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReportGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='report',
            name='group',
            field=models.ForeignKey(to='reports.ReportGroup', on_delete=django.db.models.deletion.CASCADE),
            preserve_default=True,
        ),
    ]
