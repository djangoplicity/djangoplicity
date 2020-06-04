# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

from django.conf.urls import url
from djangoplicity.iframe.views import *

urlpatterns = [
   url(r'^welcome/$', fb_welcome ),
   url(r'^discoveries/$', fb_discoveries ),
   url(r'^virtualtours/$', fb_virtualtours ),
]
