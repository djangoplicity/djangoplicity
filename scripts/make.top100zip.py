# Djangoplicity
# Copyright 2007-2010 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
import os
import tempfile
import shutil
import django

django.setup()

from djangoplicity.media.models import Image
from djangoplicity.media.options import ImageOptions
from djangoplicity.utils import optionparser
from djangoplicity.archives.contrib.queries import AllPublicQuery
from djangoplicity.archives.resources import ResourceManager


def sizeof_fmt(num):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0

if __name__ == '__main__':
    args = optionparser.get_options( [( 'o', 'output', 'Output directory', True ), ( 'f', 'format', 'Format to include', True ), ( 't', 'temp', 'Temporary directory', False ), ] )
    outputdir = os.path.expanduser( args['output'] )
    fmt = args['format'].lower()
    if args['temp']:
        tmppath = os.path.expanduser( args['temp'] )
    else:
        tmppath = None

    try:
        if not isinstance( getattr( Image.Archive, fmt ), ResourceManager ):
            raise Exception( "Specified format is not a valid resource format." )

        zipfile = "top100-%s.zip" % fmt

        if tmppath and not os.path.exists( tmppath ):
            raise Exception( "Temporary directory %s does not exists." % tmppath )

        if not os.path.exists( outputdir ):
            raise Exception( "Output directory %s does not exists." % outputdir )

        outputfile = os.path.join( outputdir, zipfile )

        # Query for images.
        ims = AllPublicQuery( browsers=[None] ).queryset( Image, ImageOptions, None )[0].filter( published=True )[:100]

        # Create temporary directory
        tmppath = tempfile.mkdtemp( dir=tmppath )
        tmppath100 = os.path.join( tmppath, "top100" )
        os.makedirs( tmppath100 )

        # Copy images into temporary directory
        copyfiles = []
        totalsize = 0
        for im in ims:
            resource = getattr( im, "resource_%s" % fmt )

            if resource and os.path.exists( resource.path ):
                ( impath, imfile ) = os.path.split( resource.path )
                copyfiles.append( ( resource.path, os.path.join( tmppath100, imfile ) ) )
                totalsize += os.path.getsize( resource.path )
            else:
                print "Warning: Resource %s for %s does not exists." % ( fmt, im.id )

        # Total file size
        print "Total uncompressed size: %s" % sizeof_fmt(totalsize)

        for ( src, dst ) in copyfiles:
            print "Copying %s to %s" % ( src, dst )
            shutil.copy( src, dst )

        # Create zip file
        os.system( "cd '%s';zip -0 -r %s top100" % ( tmppath, zipfile ) )

        # Move zip file
        zippath = os.path.join( tmppath, zipfile )
        if os.path.exists( zippath ):
            # Remove old file.
            if os.path.exists( outputfile ):
                print "Removing existing top100 file %s" % outputfile
                os.remove( outputfile )

            shutil.move( zippath, outputfile )
        else:
            raise Exception( "Couldn't generate zip file %s" % outputfile )
    except Exception, e:
        print "Error: %s" % unicode(e)
    finally:
        # Delete temporary directory if exists
        if tmppath and os.path.exists( tmppath ):
            shutil.rmtree( tmppath )
