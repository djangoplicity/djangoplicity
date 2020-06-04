from django.conf import settings

#settings.MEDIA_ROOT="/Volumes/webdocs/hubble/docs/static"

from djangoplicity.media.models import Image, ImageColor, Color

Color.objects.all().delete()

ims = Image.objects.all()
for im in ims:
    print im.id
    imcolors = Color.create_dominant_colors( im, 'resource_medium' )
    if imcolors:
        for imc in imcolors:
            print "- %s" % imc.color.name
            imc.save()