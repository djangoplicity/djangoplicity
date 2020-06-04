# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from django.conf.urls import url
from djangoplicity.contrib.admin.log.views import *

urlpatterns = [
    url( r'^$', list_admin_log_entries, name="index" ),
    url( r'^list/(?P<start>\d+)/$', list_admin_log_entries ),
]
