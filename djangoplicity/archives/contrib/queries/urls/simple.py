# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
# A simple URL scheme for browsing an archive.
#
# An example of the URLs generated for the embargo query
# for a books archive, being installed in resource/books/..
# would be::
#
#    /resource/books/archive/embargo/
#    /resource/books/archive/embargo/page/1/
#    /resource/books/archive/embargo/viewall/
#    /resource/books/archive/embargo/viewall/page/1/

# Note: These are transformed in an array of url() in get_list_urls

from djangoplicity.archives.views import archive_list

urlpatterns_template = [
    (r'$', archive_list, {  }, "%s" ),
    (r'%(page_prefix)s/(?P<page>[0-9]+)/$', archive_list, {  }, "%s_page" ),
    (r'(?P<viewmode_name>%(viewmodes)s)/$', archive_list, {}, "%s_viewmode" ),
    (r'(?P<viewmode_name>%(viewmodes)s)/%(page_prefix)s/(?P<page>[0-9]+)/$', archive_list, {}, "%s_viewmode_page" ),
]
