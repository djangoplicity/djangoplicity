from django.conf import settings
from django.apps import apps
from djangoplicity.archives.base import ArchiveModel
from djangoplicity.archives.resources import ResourceManager
import os
import shutil


def get_archive_models( app, cls=None ):
    """
    Get all defined archive models for a certain app. If cls is provided,
    only cls will be returned if it exists.
    """
    models = []

    for m in apps.get_models( app ):
        try:
            if issubclass( m, ArchiveModel ) and not m._meta.proxy and not m._meta.abstract:
                if (cls and m.__name__ == cls) or not cls:
                    models.append( m )
        except TypeError:
            pass

    return models


def get_model_resources( model ):
    """
    Get all resources defined on model
    """
    resources = []
    for attr, val in model.Archive.__dict__.items():
        if isinstance( val, ResourceManager ):
            resources.append( ( attr, val, "%s%s" % (model.Archive.Meta.resource_fields_prefix, attr), os.path.join( settings.MEDIA_ROOT, model.Archive.Meta.root, attr ) ) )
    return resources


def get_objects_files( objects, attr ):
    """
    Get all files for a specific resource referenced
    by model instances.
    """
    files = []
    for o in objects:
        res = getattr( o, attr )
        if res:
            files.append( res.path )
    return files


def get_unreferenced_files( objects, name, rm, attr, path ):
    """
    Get all unreferenced files for a certain resource.
    """
    try:
        resfiles = set([os.path.join(path, x) for x in os.listdir( path )])
    except OSError:
        resfiles = set([])
    objfiles = set(get_objects_files( objects, attr ))

    return list(resfiles - objfiles)


def clean_resource( model, res, f, backupdir=None ):
    """
    Remove a resource from the resource folder (backup instead
    of deleting if requested.
    """
    if not backupdir:
        try:
            shutil.rmtree( f, ignore_errors=True )
        except Exception:
            print "ERROR - couldn't delete %s" % f
        return
    else:
        try:
            resource_dir = os.path.join( backupdir, model.Archive.Meta.root, res )

            # Create backup dir
            if not os.path.exists( resource_dir  ):
                os.makedirs( resource_dir )

            shutil.move( f, resource_dir )
            return
        except Exception:
            print "ERROR - couldn't backup %s" % f


def clean_archive( model, cls=None, dryrun=False, backup=None ):
    """
    Remove all unreferenced files in an archive
    """
    resources = get_model_resources( model )
    objects = model.objects.all()

    for r in resources:
        print "Removing unreferenced files from %s (%s)" % (model.__name__, r[0])
        unreffiles = get_unreferenced_files( objects, *r )

        for f in unreffiles:
            print "Removing %s%s" % (f, ' (dry-run mode)' if dryrun else '')
            if not dryrun:
                clean_resource( model, r[0], f, backupdir=backup )
