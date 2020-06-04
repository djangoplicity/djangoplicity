# Djangoplicity
# Copyright 2007-2010 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from djangoplicity.archives.base import ArchiveBase, ArchiveModel
from djangoplicity.archives.resources import ResourceManager, FileType
from djangoplicity.media.models import Image, Video
from django.conf import settings
import sys,inspect



# get a list of resources for a given module, e.g thumbs etc
# returns a dictionary with key e.g thumbs
# and value ResourceManager
def get_resources_for_module (module):
    global resource_folders
    modprops = []
    for attr in dir(module.Archive):
        try:
            rm = getattr(module.Archive,attr,None)
        except AttributeError:
            pass
        if isinstance ( rm, ResourceManager):
            resource_folders.append(attr)
            modprops.append( '%s%s' % (module.Archive.Meta.resource_fields_prefix, attr) )
    return modprops



# get all files for a given object
def get_files (obj,resources):
    files = []
    for prop in resources:
        if getattr( obj, prop, None ):
            files.append( getattr( obj, prop ) )
        
    return files

    
__import__(settings.ROOT_URLCONF)
urls = sys.modules[settings.ROOT_URLCONF]


# check for ArchiveModel children in module, and process all files from all instances.
allfiles = []
resource_folders = []

for attr in dir(urls):
    mod = getattr(urls,attr)
    try:
        if issubclass ( mod, ArchiveModel):
            
            if mod == Image:
                continue
            
            resources = get_resources_for_module(mod)
            for obj in mod.objects.all():
                files = get_files(obj,resources)
                allfiles = allfiles + files
            
    
    except TypeError:
        print '!! typerr'
        pass
    
print resource_folders
print allfiles