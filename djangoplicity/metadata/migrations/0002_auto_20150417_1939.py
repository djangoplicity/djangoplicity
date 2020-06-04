# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='facility',
            name='alias',
            field=models.CharField(help_text='Alternative names, separated by ";". These names will not be shown, but used to enable search.', max_length=255, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='instrument',
            name='alias',
            field=models.CharField(help_text='Alternative names, separated by ";". These names will not be shown, but used to enable search.', max_length=255, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='subjectname',
            name='alias',
            field=models.CharField(help_text='Alternative names, separated by ";". These names will not be shown, but used to enable search.', max_length=255, blank=True),
            preserve_default=True,
        ),

        migrations.AlterField(
            model_name='facility',
            name='name',
            field=models.CharField(help_text='Can be a single name, or a list of names, separated by ";".', unique=True, max_length=255),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='facility',
            name='simbad_compliant',
            field=models.BooleanField(default=True, help_text='If "name" is a list, only the first item will be used to link to Simbad.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='instrument',
            name='name',
            field=models.CharField(help_text='Can be a single name, or a list of names, separated by ";".', unique=True, max_length=255),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='instrument',
            name='simbad_compliant',
            field=models.BooleanField(default=True, help_text='If "name" is a list, only the first item will be used to link to Simbad.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='subjectname',
            name='name',
            field=models.CharField(help_text='Can be a single name, or a list of names, separated by ";".', unique=True, max_length=255),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='subjectname',
            name='simbad_compliant',
            field=models.BooleanField(default=True, help_text='If "name" is a list, only the first item will be used to link to Simbad.'),
            preserve_default=True,
        ),
    ]
