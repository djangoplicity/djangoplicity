# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from django.conf.urls import url

from djangoplicity.archives.urls import urlpatterns_for_options
from djangoplicity.products2.options import *

from djangoplicity.products2.d2d.views import D2dModel3dList


urlpatterns = [
    url(r'd2d/$', D2dModel3dList.as_view()),
]

urlpatterns += urlpatterns_for_options( Model3dOptions )
