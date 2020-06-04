# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.contrib.sites.models import Site


def fix_name(url, type_name, name=None, enabled=None, new_url=None):
    objs = Category.objects.filter(url=url, type__name=type_name)
    category = objs[0]
    if not name is None:
        category.name = name
    if not enabled is None:
        category.enabled = enabled
    if not new_url is None:
        category.url = new_url
    category.save()


def fix_names(apps, schema_editor):
    global Category
    Category = apps.get_model('metadata', 'Category')

    if not Category.objects.all():
        return

    try:
        site = Site.objects.get_current()
    except Site.DoesNotExist:
        # If the DB is currently empty (e.g.: in the case of a new instance
        # or a DB migration we skip it
        return

    if site.domain == u'www.eso.org':
        fix_name(type_name='Images', url='logos', enabled=False)
        fix_name(type_name='Images', url='peopleandevents', name='People and Events')
        fix_name(type_name='Images', url='blackholes', name='Quasars and Black Holes')
        fix_name(type_name='Videos', url='chile', enabled=False)
        fix_name(type_name='Videos', url='e-elt', name='E-ELT')
        fix_name(type_name='Videos', url='esocast', name='ESOcast')
        fix_name(type_name='Videos', url='events', name='Events')
        fix_name(type_name='Videos', url='hd', enabled=False)
        fix_name(type_name='Videos', url='illustrations', enabled=False)
        fix_name(type_name='Videos', url='peopleandevents', name='People and Events', enabled=False)
        fix_name(type_name='Videos', url='blackholes', name='Quasars and Black Holes')
        fix_name(type_name='Videos', url='surveytelescopes', enabled=False)
    elif site.domain == u'www.spacetelescope.org':
        fix_name(type_name='Images', url='jwst', name='James Webb Space Telescope')
        fix_name(type_name='Images', url='mission', name='Launch/Servicing Missions')
        fix_name(type_name='Images', url='blackholes', name='Quasars and Black Holes')
        fix_name(type_name='Videos', url='dome', name='Dome Masters')
        fix_name(type_name='Videos', url='extrasolar', name='Exoplanets')
        fix_name(type_name='Videos', url='dvd', name='Hubble 15 Year DVD')
        fix_name(type_name='Videos', url='hubble', name='Hubble Images')
        fix_name(type_name='Videos', url='jwst', name='James Webb Space Telescope')
        fix_name(type_name='Videos', url='blackholes', name='Quasars and Black Holes')
        fix_name(type_name='Videos', url='stereoscopic', enabled=False)
        fix_name(type_name='Videos', url='vnr', enabled=False)
    elif site.domain == u'www.iau.org':
        fix_name(type_name='Images', url='e-elt', name='GA2012 - Opening Ceremony', new_url='ga2012_opening')
        fix_name(type_name='Images', url='starclusters', name='GA2012 - Closing Ceremony', new_url='ga2012_closing')
        fix_name(type_name='Videos', url='alma', name='General Assembly 2012', new_url='general_assembly_2012')
        fix_name(type_name='Videos', url='apex', name='General Assembly 2009', new_url='general_assembly_2009')
        fix_name(type_name='Videos', url='vnr', name='International Year of Light 2015', new_url='iyl')


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0003_category_enabled'),
    ]

    operations = [
        migrations.RunPython(fix_names),
    ]
