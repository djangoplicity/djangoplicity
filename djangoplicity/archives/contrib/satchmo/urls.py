# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from django.conf.urls import include, url
from djangoplicity.archives.contrib.satchmo.views import not_found_view, fb_home

urlpatterns = [
    # Overwrite some of the satchmo URLs we don't want accessible
    url( r'^history/$', not_found_view ),
    url( r'^product/view/recent/$', not_found_view ),
    url( r'^product/view/bestsellers/$', not_found_view ),
    url( r'^quickorder/$', not_found_view ),
    url( r'^search/$', not_found_view ),
    url( r'^sitemap.xml$', not_found_view ),
    url( r'^download/', not_found_view ),
    url( r'^contact', not_found_view ),
    url( r'^checkout/balance/', not_found_view ),
    url( r'^checkout/cron/$', not_found_view ),
    url( r'^checkout/mustlogin/$', not_found_view ),
    url( r'^checkout/custom/charge/', not_found_view ),

    # facebook iframe
    url( r'^fb/$', fb_home ),

    # Satchmo Shop URLs
    url(r'', include('satchmo_store.shop.urls')),
]
