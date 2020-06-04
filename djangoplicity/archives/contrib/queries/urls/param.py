# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
# A URL scheme for browsing an archive with a string parameter
#
# An example of the URLs generated for category query
# for an image archive, being installed in resource/images/..
# would be::
#
#    /resource/images/archive/category/astro/
#    /resource/images/archive/category/astro/page/1/
#    /resource/images/archive/category/astro/viewall/
#    /resource/images/archive/category/astro/viewall/page/1/
#
# "astro" is here parameteres that will be passed on to
# ArchiveQuery.queryset method as the keyword argument "stringparam".

# Note: These are transformed in an array of url() in get_list_urls

from djangoplicity.archives.views import archive_list

urlpatterns_template = (
    (r'(?P<stringparam>[-\w]+)/$', archive_list, {  }, "%s" ),
    (r'(?P<stringparam>[-\w]+)/%(page_prefix)s/(?P<page>[0-9]+)/$', archive_list, {}, "%s_page" ),
    (r'(?P<stringparam>[-\w]+)/(?P<viewmode_name>%(viewmodes)s)/$', archive_list, {}, "%s_viewmode" ),
    (r'(?P<stringparam>[-\w]+)/(?P<viewmode_name>%(viewmodes)s)/%(page_prefix)s/(?P<page>[0-9]+)/$', archive_list, {}, "%s_viewmode_page" ),
)
