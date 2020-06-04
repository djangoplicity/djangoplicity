# resets the dates, e.g. for unset release_date the creation_date will be set.

APPS = ['media','announcements','releases','products',]

from djangoplicity.archives.base import ArchiveModel
from django.db.models import Q

def import_all_archives(app,root='djangoplicity',models='models'):
    objs = []
    imprt = __import__("%s.%s.%s"% (root,app,models))
    for o in dir(eval('imprt.%s.%s' % (app,models))):
        mod = eval("imprt.%s.%s.%s" %(app,models,o))
        try:
            if issubclass(mod,ArchiveModel):
                objs.append(mod)
        except TypeError:
            pass
    return objs


def import_apps(apps):
    objs = []
    for app in apps:
        objs.extend(import_all_archives(app))       
    return objs

objs = import_apps(APPS)

print "starting"
for archive in objs:
    if hasattr(archive.Archive.Meta,'release_date') and archive.Archive.Meta.release_date:
        release_date_fieldname = archive.Archive.Meta.release_date_fieldname
        print archive
        qset = archive.objects.filter(published=True).filter(Q(release_date__isnull=True)).order_by('id').select_related()
        count = qset.count()
        print count
        for obj in qset:
            #if not getattr(obj,release_date_fieldname):
            setattr(obj,release_date_fieldname,obj.created)
            count -= 1
            print "%d: %s %s" % (count,obj.id,getattr(obj,release_date_fieldname))
            obj.save()