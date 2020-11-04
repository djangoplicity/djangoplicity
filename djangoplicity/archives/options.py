# coding: utf-8
#
# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

from builtins import str
from builtins import object
import operator

from django.conf import settings
from django.conf.urls import url
from django.core.exceptions import ImproperlyConfigured
from django.db import connection, models
from django.shortcuts import redirect

from djangoplicity.archives.contrib.search.queryparser import \
    AstronomyQueryParser
from djangoplicity.archives.views import archive_detail
from functools import reduce
#from django.db.models.query import QuerySet
#from django.utils.text import smart_split

if settings.USE_I18N:
    from djangoplicity.translation.models import TranslationModel
    from django.utils import translation  # pylint: disable=ungrouped-imports

__all__ = ('ArchiveOptions',)


class ArchiveOptions(object):
    # Title of archive.
    title = None

    # Absolute URL of an image
    opengraph_image = None

    # The default template for the downloadable resources - template
    # will be included in other templates
    description_template = 'archives/object_description.html'

    # The default template for the downloadable resources - template
    # will be included in other templates
    resources_template = 'archives/object_resources.html'

    # The default template for the object info - template will
    # be included in other templates.
    info_template = 'archives/object_info.html'

    # The default template for the object admin - template will
    # be included in other templates.
    admin_template = 'archives/object_admin.html'

    # The full name of a template to use in rendering the detail page. This
    # lets you override the default template name.

    # If template_name isn't specified, this view will use the
    # template <app_label>/<model_name>/detail.html or
    # <app_label>/detail.html by default.
    template_name = None

    # The name of a field on the object whose value is the template name to
    # use. This lets you store template names in the data. In other words,
    # if your object has a field 'the_template' that contains a string 'foo.html',
    # and you set template_name_field to 'the_template', then the generic view
    # for this object will use the template 'foo.html'.
    template_name_field = None

    # The MIME type to use for the resulting document. Defaults to the value
    # of the DEFAULT_CONTENT_TYPE setting.
    content_type = None

    slug_field = 'id'

    slug_urls = True

    related_release_date = None
    related_embargo_date = None

    # Optional list or tupple of fields to be used in the querysets
    # as select_related() and prefetch_related()
    # Warning: prefetching might not work for translations: Django will
    # prefetch based on the current key (i.e. the translation key) and will
    # not find e.g. ManyToMany made with the source foreign key.
    # To fix this would require updating the behaviour of prefetch_related
    select_related = None
    prefetch_related = None

    # Optional list of fields, if specified then only these fields will be
    # fetched by archive_list. This can considerably speed up queries, but
    # must be used with care as fields not included but used in the template
    # will generate additional queries
    archive_list_only_fields = None

    class Queries( object ):
        pass

    class Browsers( object ):
        pass

    class Import( object ):
        pass

    class ResourceProtection( object ):
        pass

    #@property
    @classmethod
    def default_query( cls ):
        """ Get the default query for the archive. """
        # First determine name.
        try:
            default_q_name = cls.Queries.Meta.default
        except AttributeError:
            default_q_name = 'default'

        # Now try to retrieve the attribute.
        try:
            return getattr( cls.Queries, default_q_name )
        except AttributeError:
            return None

    @staticmethod
    def process_object_list( object_list ):
        """ Hook for pre-processing the object list """
        pass

    @staticmethod
    def extra_context( obj, lang=None ):
        """
        Hook for adding extra context variables to the detail page in the archive.

        Return a dictionary of values to add to the template context. By default, this
        is an empty dictionary. If a value in the dictionary is callable, the
        generic view will call it just before rendering the template.
        """
        if settings.USE_I18N:
            if isinstance( obj, TranslationModel ):
                lang = translation.get_language() if lang is None else lang
                return {
                    'translations': obj.get_translations(),
                }
        return {}

    @staticmethod
    def has_staging_perms( request, obj=None ):
        """
        Determine if the given request is authorized to view staging archive items.
        By default any logged in user can login.
        """
        return request.user.is_superuser or request.user.is_staff
        #  return request.user.is_superuser or \
        #      (request.user.is_staff and not request.user.has_perm("%s.view_released_%ss_only" % (admin_instance.model._meta.app_label, admin_instance.model._meta.model_name.replace('proxy', '')))

    @staticmethod
    def has_embargo_perms( request, obj=None ):
        """
        Determine if the given request is authorized to view embargoed archive items.
        By default any logged in user can login.
        """
        return request.user.is_authenticated

    @staticmethod
    def has_admin_perms( request, obj=None ):
        """
        Determine if the given request is authorized to edit archive items.
        By default any staff user is assumed to have edit rights.

        Return value must be a two tuple. First element a boolean value
        that determines if the user has admin rights to the object or not.
        The second value is a list of strings, to specify additional cache
        parameters.
        """
        return ( request.user.is_staff, ['admin'] if request.user.is_staff else [] )

    @staticmethod
    def detail_queryset( model, lang=None ):
        """
        Returns a QuerySet of all model instances that can be show in a detail view. This method
        should return all objects (e.g. also unpublished) that can be shown - staging and
        embargoed and other permission logic happens in the view and not here.

        Usually you want to override this method for selecting related objects.
        """
        qs = None

        if settings.USE_I18N:
            if issubclass( model, TranslationModel ):
                lang = translation.get_language() if lang is None else lang
                qs = model.objects.language( lang ).all()

        if qs is None:
            qs = model.objects.all()

        return qs

    @classmethod
    def detail_notfound( cls, model, **filter_kwargs ):
        """
        In case a matching object is not found for a given query in the current
        language, look for an object which is a translation "source" (i.e.:
        just look for the ID without language filtering)
        """
        if settings.USE_I18N:
            if issubclass( model, TranslationModel ):
                try:
                    filter_kwargs['source__isnull'] = True
                    return model.objects.filter( **filter_kwargs ).get()
                except model.DoesNotExist:
                    pass
        return None

    @classmethod
    def detail_redirect( cls, model, **filter_kwargs ):
        """
        In case a matching object is not found for query, allow this method to return a special response to the user.

        Currently this is only used to direct translation
        """
        if settings.USE_I18N:
            if issubclass( model, TranslationModel ):
                lang = translation.get_language()
                if lang != settings.LANGUAGE_CODE:
                    try:
                        obj = cls.detail_queryset( model, lang=settings.LANGUAGE_CODE ).filter( **filter_kwargs ).get()
                        return redirect( obj )
                    except model.DoesNotExist:
                        pass
        return None

    @classmethod
    def get_detail_urls( cls, name_prefix="", extra_options="", detail_view=None ):
        """
        Return URL patterns for the detail view.
        """
        options = cls
        detail_view.options = options

        if options.slug_urls:
            urlpatterns = [ url(r'^%s(?P<slug>[-\w]+)/$' % settings.ARCHIVE_URL_DETAIL_PREFIX, archive_detail, { 'detail_view': detail_view }, name=name_prefix ) ]
        else:
            urlpatterns = [ url(r'^%s(?P<object_id>[0-9]+)/$' % settings.ARCHIVE_URL_DETAIL_PREFIX, archive_detail, { 'detail_view': detail_view }, name=name_prefix ) ]

        # Install extra detail views
        main_detail_view = detail_view
        if hasattr( options, 'detail_views' ):
            detail_views = options.detail_views

            for v in detail_views:
                if not isinstance(v['view'], type(main_detail_view)):
                    raise ImproperlyConfigured("Extra detail view must be a subclass of %s." % type(main_detail_view))

                detail_view = v['view']
                detail_view.options = options

                if options.slug_urls:
                    urlpatterns += [ url(r'^%s(?P<slug>[-\w]+)/%s$' % ( settings.ARCHIVE_URL_DETAIL_PREFIX, v['url_pattern'] ), archive_detail, { 'detail_view': detail_view }, name="%s_%s" % ( name_prefix, v['urlname_suffix'] ) ) ]
                else:
                    urlpatterns += [ url(r'^%s(?P<object_id>[0-9]+)/%s$' % ( settings.ARCHIVE_URL_DETAIL_PREFIX, v['url_pattern'] ), archive_detail, { 'detail_view': detail_view }, name="%s_%s" % ( name_prefix, v['urlname_suffix'] ) ) ]

        return urlpatterns

    @classmethod
    def search( cls, request, qs, searchstr, queryparserclass=AstronomyQueryParser, **kwargs ):
        """
        Hook to do keyword search through the rows in a query set.

        class SomeArchiveOptions( ArchiveOptions ):
            search_fields = ('id','fk__attr', '^title', '=title', '@title' )

            class Queries:
                default = SomeQuery( searchable=True )

        """

        # Check options
        if not hasattr(cls, 'search_fields'):
            raise ImproperlyConfigured("The field search_fields must be specified in ArchiveOptions for enabling keyword search.")

        # Extract search parameters and parse query.
        # Criterions are mandatory(+) by default, unless specifically excluded (-)
        # or special queries such as "messier 7" which will return two optional
        # criterions: "MESSIER 7" and "MESSIER7"

        criteria = queryparserclass.parse( searchstr )

        # Apply search criteria.
        mandatory = []
        nonmandatory = []

        for c in criteria:
            # mandatory.append( c )
            if c.is_mandatory():
                mandatory.append( c )
            else:
                nonmandatory.append( c )

        # Build search query (helper mehtods)
        def construct_search( field_name ):
            if connection.vendor == 'postgresql' and \
                    'django.contrib.postgres' in settings.INSTALLED_APPS:
                # Use Postgres Unaccent module
                field_name = field_name + '__unaccent'

            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        def construct_criteria_search( criteria ):
            or_queries = [models.Q( **{ construct_search( str( field_name ) ): criteria.keyword } ) for field_name in cls.search_fields]
            or_queries = reduce(operator.or_, or_queries)
            return or_queries

        # TODO: take care of several search_fields. Currently only takes care of a single search field.

        # Mandatory keywords (AND'ed together and can possibly be negated)
        and_queries_incl = []
        and_queries_excl = []
        for c in mandatory:
            if c.is_include():
                and_queries_incl.append( construct_criteria_search( c ) )
            else:
                and_queries_excl.append( construct_criteria_search( c ) )

        if and_queries_incl:
            qs = qs.filter( reduce(operator.and_, and_queries_incl) )

        if and_queries_excl:
            qs = qs.exclude( reduce(operator.and_, and_queries_excl) )

        # Non-mandatory keywords (OR'ed together)
        or_queries = []
        for c in nonmandatory:
            or_queries.append( construct_criteria_search( c ) )

        if or_queries:
            qs = qs.filter( reduce(operator.or_, or_queries) )

        # Ensure proper results when search related models as well.
        for field_name in cls.search_fields:
            if '__' in field_name:
                qs = qs.distinct()
                break

        return qs
