# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from django.conf.urls import url
from djangoplicity.archives.contrib.satchmo.freeorder.views import *

urlpatterns = [
   url(r'$', free_order_request, {}, 'free_order_form'),
]
