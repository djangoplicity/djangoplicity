# Djangoplicity
# Copyright 2007-2010 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

"""
Script used to created archive directories.

Dry run example (will read MEDIA_ROOT and ARCHIVE_IMPORT_ROOT settings)::
    python ../djangoplicity/scripts/archive.create.dirs.py -n

Create directories for a specific app:  
    python ../djangoplicity/scripts/archive.create.dirs.py -n -a media
    
Create directories for a specific archive:  
    python ../djangoplicity/scripts/archive.create.dirs.py -n -a media -m Image

"""

from djangoplicity.utils import optionparser
from djangoplicity.archives.base import ArchiveModel
from djangoplicity.archives.resources import ResourceManager, FileType
from django.db import models
from django.conf import settings
import os
import sys
from django.core.exceptions import ImproperlyConfigured

def create_dirs( output, output_import, model, options, dryrun=False ):
    """
    Function to create all needed directories for archives
    """
    try:
        archive_root = os.path.join( output, model.Archive.Meta.root )

        for attr in dir( model.Archive ):
            val = getattr( model.Archive, attr )
            if isinstance( val, ResourceManager ):
                resdir = os.path.join( archive_root, attr )
                if not os.path.exists( resdir ):
                    print "Creating dir %s" % resdir
                    if not dryrun:
                        os.makedirs( resdir )
                else:
                    print "- Existing dir %s" % resdir
                    pass
                    
        if output_import and options and hasattr( options.Import, 'scan_directories' ):
            archive_import_root = os.path.join( output_import, options.urlname_prefix )
            
            for fmt, allowed_exts in options.Import.scan_directories:
                if not hasattr( model.Archive, fmt ):
                    continue
                                
                resdir = os.path.join( archive_import_root, fmt )
                if not os.path.exists( resdir ):
                    print "Creating import dir %s" % resdir
                    if not dryrun:
                        os.makedirs( resdir )
                else:
                    #print "- Existing import dir %s" % resdir
                    pass
    except AttributeError:
        pass

def get_archive_options( model ):
    """
    Get the archive options for a model
    """
    dotname = "%s.%s" % ( model.__module__, model.__name__ )
    for m, o in settings.ARCHIVES:
        if m == dotname:
            try:
                modname = ".".join( o.split(".")[:-1] )
                optname = o.split(".")[-1]
                module = __import__( modname, {}, {}, ['optname'] )
                return getattr( module, optname )
            except (ImportError, AttributeError):
                pass
    return None

if __name__ == '__main__':
    args = optionparser.get_options( [
        ( 'a', 'app', 'Django app used for creating the directories', False, { 'default' : '' } ),
        ( 'o', 'output', 'Output directory', False, { 'default' : settings.MEDIA_ROOT } ),
        ( 'i', 'import', 'Output directory for import dirs', False, { 'default' : settings.ARCHIVE_IMPORT_ROOT } ),
        ( 'm', 'model', 'Specific archive model', False ),
        ( 'n', 'dry-run', 'Do not actually create the directories', False, { 'action' : 'store_true', 'default' : False } )     
    ] )
    
    try:
        if args['model'] and args['app']:
            m = models.get_model( args['app'], args['model'] )
            if m:
                m = [m]
            else:
                raise ImproperlyConfigured
        elif args['app']:
            a = models.get_app( args['app'] )
            m = models.get_models( app_mod=a )
        else:
            m = models.get_models()
    except ImproperlyConfigured:
        print "Error: Invalid app or model specified"
        sys.exit(1)
        
    # Loop over installed applications
    for model in m:
        options = get_archive_options( model )
        if model and issubclass( model, ArchiveModel ) and not model._meta.proxy and not model._meta.abstract and hasattr( model, 'Archive' ):
            create_dirs( args['output'], args['import'], model, options, dryrun=args['dry-run'] )
