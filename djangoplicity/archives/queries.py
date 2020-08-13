# coding: utf-8
#
# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#


from past.builtins import basestring
from builtins import object
from datetime import datetime

from django.conf.urls import include, url
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

if settings.USE_I18N:
    from djangoplicity.translation.models import TranslationModel
    from django.utils import translation

__all__ = ('ArchiveQuery', )


def urlname_for_query( options, query, query_name, browser=False ):
    """
    """
    # Determine which query is the default one
    try:
        default_q_name = options.Queries.Meta.default
    except AttributeError:
        default_q_name = 'default'

    # Get urlname_prefix
    if not hasattr( options, 'urlname_prefix' ):
        return None

    urlname_prefix = options.urlname_prefix

    if default_q_name != query_name:
        if browser:
            return '%s_query_%s_viewmode' % ( urlname_prefix, query_name )
        else:
            return '%s_query_%s' % ( urlname_prefix, query_name )
    else:
        if browser:
            return '%s_defaultquery_viewmode' % ( urlname_prefix )
        else:
            return '%s_defaultquery' % ( urlname_prefix )


class ArchiveQuery(object):
    """ """

    def __init__(self, verbose_name=None, searchable=False, viewmode_param=None, browsers=None, include_in_urlpatterns=None, url_include=None, url_template=None, extra_templates=None, search_default=True, feed_name=None, select_related=None, sort_fields=[] ):
        """
            verbose_name -
            searchable - Specifies if keyword search can be used to search the query.
            viewmode_param - Determine is the viewmode for this query can be determined by the GET parameter.
            include_in_urlpatterns - Determines if urlpatterns_for_options should include this query in
                when generating the URLconf for the archive.
            url_template - A module name containing a variable called urlpatterns_template.
            url_include - If not url_template is set, this option should be set to a module name with a normal URLconf
                which will be included.
            search_default - Determines if default search should be used instead if query is not searchable.

        """
        self._verbose_name = verbose_name
        self.searchable = searchable
        self.search_default = search_default
        self.viewmode_param = viewmode_param
        if browsers is None:
            raise ImproperlyConfigured(_('At least one browser must be specified for an archive query.'))
        self.browsers = browsers
        self.default_browser = self.browsers[0]
        self.include_in_urlpatterns = include_in_urlpatterns or False
        self.url_include = url_include
        self.url_template = url_template
        self.extra_templates = extra_templates
        self.feed_name = feed_name
        self.select_related = select_related
        self.sort_fields = sort_fields

    def ordering( self, model, request ):
        """
        Determine the ordering of the data based on user request.
        """
        order = []
        sort_fields = self.sort_fields if self.sort_fields else ( model.Archive.Meta.sort_fields if hasattr( model.Archive.Meta, 'sort_fields') else [] )

        if request and "sort" in request.GET and sort_fields:
            s = request.GET["sort"]
            fs = s.split(",")
            for f in fs:
                f = f.strip()
                if len(f) > 0:
                    tmp = f[1:] if f[0] == "-" else f
                    if tmp in sort_fields:
                        order.append( f )
        return order

    def queryset(self, model, options, request, only_source=False, mode='fallback', **kwargs ):
        """
        Hook to specify the queryset for this query.

        Care should be taken not to evaluate the query set, since e.g. the list
        view will do further filtering, and at the very least pagination will take
        place, so only a limited amount of rows are fetched from the database.

        Must return a 2-tuple where first element is the query set and second
        element is any additional extra data in form of a dict, that can be useful
        to other methods in the query (e.g. verbose_name() ).

        An Http404 exception should be thrown from the method, in case the query
        cannot be satisfied - e.g. if invalid parameters are passed in as keyword
        arguments.

        An ImproperlyConfigured exception should be thrown in case the Query class
        was not properly configured.

        Also, in subclasses you should normally ensure to call the super method first
        and then do additionally filtering (note, there naturally might be cases where
        this is not desired, but this is normally an exception).

        Mode can specified to be either 'fallback' in which case original
        content will be retrieved if no translation exist, or 'language' which
        will only return translated content
        """
        qs = None

        if settings.USE_I18N:
            if issubclass( model, TranslationModel ):
                if not only_source:
                    lang = translation.get_language()

                    if mode == 'fallback':
                        qs = model.objects.fallback(lang).all()
                    elif mode == 'language':
                        qs = model.objects.language(lang).all()
                    else:
                        raise Exception('Unkown queryset mode: "%s"' % mode)

        if qs is None:
            qs = model._default_manager.get_queryset()

        # Select related fields if necessary
        if self.select_related:
            if isinstance(self.select_related, basestring):
                self.select_related = (self.select_related, )

            qs = qs.select_related( *self.select_related )

        # Order query set
        order = self.ordering( model, request )
        if order:
            qs = qs.order_by( *order )

        return ( qs, {} )

    def has_permissions(self, request):
        """ Hook to determine if a request is allowed to view this query. """
        return True

    def has_browser(self, name):
        """ Hook to determine if query is allowed to use the browser given by the name. """
        return name in self.browsers

    def check_parameters(self, model, options, request):
        """
        Hook to check if parameters (e.g. GET) are neccessary.
        Returns a redirect URL if necessary, or '' if OK
        """
        return ''

    def verbose_name(self, **kwargs ):
        """
        Method that can be overwritten to customize the archive title.

        Method will receive any keyword arguments that the queryset
        desire to pass on.
        """
        return _( self._verbose_name )

    def url_args(self, model, options, request, **kwargs ):
        """
        Hook for query to specify extra reverse URL lookup arguments.
        """
        return []

    def get_list_urls(self, url_prefix="", name_prefix="", extra_options={}):
        r"""
        Get URL patterns for query.

        General URL generator which takes a urlpatterns_template and returns a urlpatterns.
        For instance a module djangoplicity.archives.contrib.queries.url.simple should include::

            urlpatterns_template = (
                (r'$', archive_list, { 'viewmode_name': 'normal' }, "%s_default" ),
                (r'page/(?P<page>[0-9]+)/$', archive_list, { 'viewmode_name': 'normal'  }, "%s_default_page" ),
                (r'(?P<viewmode_name>[-\w]+)/$', archive_list, {}, "%s_viewmode" ),
                (r'(?P<viewmode_name>[-\w]+)/page/(?P<page>[0-9]+)/$', archive_list, {}, "%s_viewmode_page" ),
            )

        The result will be an urlpatterns like this::
            urlpatterns = (
                url(r'<url_prefix>$', archive_list, { 'viewmode_name': 'normal', 'query_name': <query_name> }, "<name_prefix>_default" ),
                url(r'<url_prefix>page/(?P<page>[0-9]+)/$', archive_list, { 'viewmode_name': 'normal', 'query_name': <query_name>  }, "<name_prefix>_default_page" ),
                url(r'<url_prefix>(?P<viewmode_name>[-\w]+)/$', archive_list, {'query_name': <query_name>}, "<name_prefix>_viewmode" ),
                url(r'<url_prefix>(?P<viewmode_name>[-\w]+)/page/(?P<page>[0-9]+)/$', archive_list, {'query_name': <query_name>}, "<name_prefix>_viewmode_page" ),
            )

        Worth nothing:
            - <url_prefix> is ending with a slash.
            - query_name is automatically added as an extra option.
            - The URL pattern name will get the <name_prefix> inserted.
        """
        urlpatterns = []

        if self.url_template is not None:
            # Get templates
            template = __import__(self.url_template, {}, {}, ['']).urlpatterns_template
            viewmodespattern = "|".join( self.browsers )

            # Iterate over each element, and add a pattern.
            for p in template:
                url_suffix = p[0] % { 'page_prefix': settings.ARCHIVE_PAGINATOR_PREFIX, 'viewmodes': viewmodespattern }
                view = p[1]
                options = {}
                options.update( extra_options )
                try:
                    options.update(p[2])
                    name = p[3] % name_prefix
                except IndexError:
                    name = None

                urlpatterns += [url( r'%s%s' % (url_prefix, url_suffix ), view, options, name=name )]
        else:
            urlpatterns += [url( url_prefix, include( self.url_include ), extra_options )]

        return urlpatterns

    @staticmethod
    def _filter_datetime( queryset, common_now=None, datetime_feature='release_date', unpublished=False, null_values=True ):
        """ Helper method to filter a query set for embargoed items. """
        now = common_now or datetime.now()
        if getattr( queryset.model.Archive.Meta, datetime_feature, False ):
            fieldname = getattr( queryset.model.Archive.Meta, '%s_fieldname' % datetime_feature )
            if unpublished:
                q = Q( **{'%s__gt' % fieldname: now } )
            else:
                q = Q( **{'%s__lte' % fieldname: now } )
            if null_values:
                q = q | Q( **{'%s__isnull' % fieldname: True } )
            queryset = queryset.filter( q )
        return queryset

    @staticmethod
    def _filter_datetime_by_fieldname( queryset, common_now=None, fieldname=None, unpublished=False, null_values=True ):
        """ Helper method to filter a query set for embargoed items. """
        now = common_now or datetime.now()
        if fieldname:
            if unpublished:
                q = Q( **{'%s__gt' % fieldname: now } )
            else:
                q = Q( **{'%s__lte' % fieldname: now } )
            if null_values:
                q = q | Q( **{'%s__isnull' % fieldname: True } )
            queryset = queryset.filter( q )
        return queryset
