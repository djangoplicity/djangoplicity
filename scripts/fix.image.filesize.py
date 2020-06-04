from django.conf import settings
import os
from djangoplicity.metadata.consts import get_file_type

#settings.MEDIA_ROOT="/Volumes/webdocs/hubble/docs/static"

from djangoplicity.media.models import Image

ims = Image.objects.filter()
for im in ims:
    if im.resource_original:
        try:
            im.file_size = int( os.path.getsize( im.resource_original.path ) / 1024 )
            im.file_type = get_file_type( im.resource_original.path )
            im.save()
            print "%s (%s): %s" % (im.id, im.file_type, im.file_size/1024 )
        except Exception, e:
            print "ERROR %s" % im.id
            print e