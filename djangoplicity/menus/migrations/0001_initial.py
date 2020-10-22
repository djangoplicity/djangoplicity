# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Menu',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('hide_menu_root', models.BooleanField(default=True, help_text='Defines if the root menu item should be hidden (a menu always have exactly one root menu item).')),
                ('expansion_depth', models.PositiveSmallIntegerField(default=0, help_text='Defines the default expansion level of the menu. Use e.g. 2 to show the first two levels in the menu. A value of 0 shows the entire menu. This field can be overridden by the template.')),
                ('max_depth', models.PositiveSmallIntegerField(default=0, help_text='Defines the maximum number of levels allowed in the menu. A value of 0 means no limits. This field can be overridden by the template.')),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MenuItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('link', models.CharField(help_text="Use lower-case letters only. Local links should start with forward slash, and normally ends with slash - eg /science/. Remote links should be full URLs - eg http://www.cnn.com/. The field can be left empty, in which case the menu item won't be linked.", max_length=255, blank=True)),
                ('published', models.BooleanField(default=True)),
                ('on_click', models.PositiveIntegerField(default=0, choices=[(0, 'Same window'), (1, 'New window')])),
                ('is_primary', models.BooleanField(default=True, help_text='In case a menu contains several items with the same link, set this field to true and the others menu items field to false, to control which item is used for item highlighting and breadcrumb generation.')),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('menu', models.ForeignKey(blank=True, to='menus.Menu', help_text='This field only have effect for the root menu item', null=True, on_delete=models.deletion.CASCADE)),
                ('parent', models.ForeignKey(related_name='children', blank=True, to='menus.MenuItem', help_text='Moving a node to a new parent, will place it as the last node. When moving a menu item, all of it sub-items will be moved as well.', null=True, on_delete=models.deletion.CASCADE)),
            ],
            options={
                'ordering': ['tree_id', 'lft'],
            },
            bases=(models.Model,),
        ),
    ]
