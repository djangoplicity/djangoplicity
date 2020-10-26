# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminComment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('comment', models.TextField(blank=True)),
                ('object_id', models.SlugField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=django.db.models.deletion.CASCADE)),
                ('user', models.ForeignKey(blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True, on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
                'ordering': ['-timestamp', 'content_type', 'object_id'],
            },
            bases=(models.Model,),
        ),
    ]
