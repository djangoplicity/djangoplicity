# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from django.conf import settings
from django.conf.urls import url
from djangoplicity.archives.queries import ArchiveQuery
from djangoplicity.archives.contrib.search.views import archive_search_form
from djangoplicity.archives.views import GenericDetailView

__all__ = ('urlpatterns_for_options',)


def urlpatterns_for_options( options, urlpatterns=None ):
    """
    Create URL patterns for an archive based on the options for the
    archive. Installs URL patterns for each archive query in the options.
    Each archive query determines itself if it want to be include in the patterns,
    and which url scheme it wants to be based on. See URL schemes in
    djangoplicity.archives.contrib.queries.urls.

    A default query will try to be determined. Unless otherwise specified
    the default query is named 'default' and will be installed as detailed
    below. It will also be given the name, '<urlname_prefix>_default_query'

    The detail query will be named '<urlname_prefix>_detail'

    The general URL scheme produced by this function is::

        .../archive/<query_name>/... --> URL scheme for query.
        .../detail/<slug or object id>/ --> Detail for archive item.
        .../ --> URL scheme for query named 'default'.

    Whether a slug or an object id is used for detail view is determined
    by ArchiveOptions.slug_urls.

    The following settings options sets the names used in the above general
    URL scheme::
        settings.ARCHIVE_URL_QUERY_PREFIX = 'archive'
        settings.ARCHIVE_URL_DETAIL_PREFIX = 'detail'
        settings.ARCHIVE_URL_FEED_PREFIX = 'feed'

    Note, when defining above names, care should be taken not to collide with
    the URL scheme for the default query if one such is defined.
    """
    attrs = options.Queries.__dict__

    # Determine which query is the default one
    try:
        default_q_name = options.Queries.Meta.default
    except AttributeError:
        default_q_name = 'default'

    # Determine if object_id or slug is used
    if hasattr( options, 'urlname_prefix' ):
        urlname_prefix = options.urlname_prefix
    else:
        urlname_prefix = None

    # Find all queries to include - also determine
    queries = {}
    for a, q in attrs.items():
        if isinstance(q, ArchiveQuery):
            if q.include_in_urlpatterns:
                queries[a] = q

    if urlpatterns is None:
        urlpatterns = []

    # Install URLS for all queries
    for qname, q in queries.items():
        if qname == default_q_name:
            name_prefix = '%s_defaultquery' % urlname_prefix
            url_prefix = r'^'
            extra_options = { 'query_name': default_q_name }
        else:
            name_prefix = '%s_query_%s' % (urlname_prefix, qname)
            url_prefix = r'^%s/%s/' % (settings.ARCHIVE_URL_QUERY_PREFIX, qname)
            extra_options = { 'query_name': qname }

        urlpatterns += q.get_list_urls( url_prefix=url_prefix, name_prefix=name_prefix, extra_options=extra_options )

    # Install extra syndication views (before so 'feed' keyword is not read by detail view)
    if hasattr(options, 'feeds'):
        name_prefix = "%s_%s" % ( urlname_prefix if urlname_prefix else None, settings.ARCHIVE_URL_FEED_PREFIX )
        feed_dict = options.feeds()
        if feed_dict:
            for name, feedklass in feed_dict.items():
                # Delegate to each feed class to generate their URLs
                urlpatterns += feedklass.get_feed_urls( name=name, url_prefix=settings.ARCHIVE_URL_FEED_PREFIX, name_prefix=name_prefix )

    # install query for advanced search
    if settings.ENABLE_ADVANCED_SEARCH and hasattr(options, 'AdvancedSearch'):
        urlname = "%s_%s" % (urlname_prefix if urlname_prefix else None, settings.ARCHIVE_URL_SEARCH_PREFIX)
        urlpatterns += [ url( r'^search/$', archive_search_form, { 'options': options }, name=urlname) ]

    # Install query for detail view
    urlpatterns += options.get_detail_urls(
        name_prefix="%s_detail" % urlname_prefix if urlname_prefix else None,
        detail_view=getattr(options, 'detail_view', GenericDetailView)()
    )

    return urlpatterns


def _has_template( q ):
    """ Determine if a query has a template given. """
    return q.url_template is not None
