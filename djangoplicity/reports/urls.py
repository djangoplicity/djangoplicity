# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from django.conf.urls import url
from djangoplicity.reports.views import *

# URL config for overwriting the default change view of the reports module.
# See notes in views.py for usage guide.

urlpatterns = [
    url(r'^report/(?P<report_id>\d+)/$', report_detail, name='report-detail'),
 ]
