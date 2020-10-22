import csv
import re
import os
import shutil

from djangoplicity.archives.resources import ResourceManager

from djangoplicity.products.models import Application, Handout, MiniSite, PaperModel, PlanetariumShow, VirtualTour, KidsDrawing, PressKit, ConferencePoster, Logo, OnlineArtAuthor, OnlineArt, SlideShow, ElectronicCard, Exhibition, FITSImage, UserVideo, Presentation, AnnualReport, EducationalMaterial, CDROM, Book, Brochure, Merchandise, Periodical, PostCard, MountedImage, Poster, Sticker, TechnicalDocument, Calendar, IMAXFilm, ConferenceItem, Visit, Apparel, CapJournal, Messenger, ScienceInSchool, Bulletin, Flyer, Handout, Map, PrintedPoster, ElectronicPoster

import djangoplicity.products.options

import django
if django.VERSION >= (2, 2):
    from django.urls import NoReverseMatch
else:
    from django.core.urlresolvers import NoReverseMatch

exclude_fields = ('low_stock_level', 'reserve_count', 'stock', 'delivery_date', 'type', 'product')

def migrate(obj, new_id, models, options ):

    new_model = None

    for model in models:
        if new_id.startswith(model + '_'):
            new_model = models[model][0]

    if new_model:
        print 'Migrating: %s (%s) -> %s' % (obj.id, obj.__class__.__name__, new_id)

        # Generate dict of fields to copy over:
        kwargs = {}
        for key in obj._meta.get_all_field_names():
            if key == 'id':
                kwargs['id'] = new_id
                continue
            if key in exclude_fields:
                continue
            try:
                kwargs[key] = getattr(obj, key)
            except AttributeError:
                pass

        n = new_model(**kwargs)
        n.save()

        # Move resources
        resource_names = filter( lambda x: isinstance( getattr( obj.Archive, x ), ResourceManager ), dir(obj.Archive) )

        for rname in resource_names:
            resource = getattr( obj, "resource_%s" % rname )

            if resource:
                dst_options = getattr(djangoplicity.products.options, '%sOptions' % n.__class__.__name__)

                directory = resource.path.replace('/archives/%s/' % options.urlname_prefix, '/archives/%s/' % dst_options.urlname_prefix)

                directory = os.path.dirname( directory )
                oldname = os.path.basename( resource.path )
                base, ext = os.path.splitext( oldname )
                newname = "%s%s" % ( n.id, ext )
                newpath = os.path.join( directory, newname )
                print '    Moving: %s -> %s' % (resource.path, newpath)
# FIXME
                try:
                    shutil.copy( resource.path, newpath )
                except IOError:
                    print '        (FAIL)'

        # Delete the old product
        old_url = obj.get_absolute_url()
        obj.delete()

# FIXME
        # import sys
        # sys.exit()

        return n

    else:
        print 'Renaming: %s (%s) -> %s' % (obj.id, obj.__class__.__name__, new_id)

        obj = obj.rename(new_id)
        obj.save()

        return obj


f = open('/tmp/inv.csv')

models = {
    'apparel': (Apparel, Merchandise),
    'capj': (CapJournal, Periodical),
    'messenger': (Messenger, Periodical),
    'sis': (ScienceInSchool, Periodical),
    'bulletin': (Bulletin, Periodical),
    'flyer': (Flyer, Brochure),
    'handout': (Handout, Brochure),
    'map': (Map, Brochure),
#   'report': (Report, TechnicalDocument), ???
    'print_poster': (PrintedPoster, Poster),
    'conf_poster': (ConferencePoster, Poster),
    'elec_poster': (ElectronicPoster, Poster),
}

products = {}

reader = csv.reader(f)
for row in reader:
    new_id = row[1]

    m = re.search('^https://www.eso.org/public/products/([^/]+)/([^/]+)/$', row[20])

    if not m:
        continue
    typ = m.group(1)
    old_id = m.group(2)

    # Handle special cases in URLs:
    if typ == 'dvds':
        typ = 'cdroms'
    if typ == 'reports':
        typ = 'techdocs'

    products['%s:%s' % (typ, old_id)] = (typ, new_id)


missing_products = []

# TODO:
# We ignore the exhibitions for now, they should be added back once the spreadshee it updated
# Exhibition,

missing = open('/tmp/missing', 'w')
redirect = open('/tmp/redirect', 'w')

for model in Application, Handout, MiniSite, PaperModel, PlanetariumShow, VirtualTour, KidsDrawing, PressKit, ConferencePoster, Logo, OnlineArtAuthor, OnlineArt, SlideShow, ElectronicCard, FITSImage, UserVideo, Presentation, AnnualReport, EducationalMaterial, CDROM, Book, Brochure, Merchandise, Periodical, PostCard, MountedImage, Poster, Sticker, TechnicalDocument, Calendar, IMAXFilm, ConferenceItem, Visit:
    for obj in model.objects.all():
        options = getattr(djangoplicity.products.options, '%sOptions' % obj.__class__.__name__)

        key = '%s:%s' % (options.urlname_prefix, obj.id)

        if key not in products:
            missing_products.append(obj)

            try:
                url = 'https://www.eso.org%s' % obj.get_absolute_url()
            except (AttributeError, NoReverseMatch):
                url = ''
            missing.write('%s,%s,%s\n' % (obj.__class__.__name__, obj.id, url))
            continue

        old_url = obj.get_absolute_url()

        obj = migrate(obj, products[key][1], models, options)
        redirect.write('%s,%s\n' % (old_url, obj.get_absolute_url()))

missing.close()
