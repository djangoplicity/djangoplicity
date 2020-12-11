# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from builtins import str
from builtins import filter
from datetime import datetime
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, FieldError
from django.db.models import Q
from django.db.models.fields.related import ForeignKey
from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from djangoplicity.archives.queries import ArchiveQuery
from djangoplicity.archives.contrib.search import *

__all__ = ( 'AllPublicQuery', 'UnpublishedQuery', 'EmbargoQuery', 'StagingQuery', 'CategoryQuery', 'YearQuery', 'FeaturedQuery',
        'AdvancedSearchQuery', 'param_extra_templates', 'simple_extra_templates', 'ForeignKeyQuery' )

CATEGORY_RELATION_FIELD = 'category'
CATEGORY_URL_FIELD = 'url'
CATEGORY_TITLE_FIELD = 'name'


def simple_extra_templates( model, query, query_name, query_data ):
    """
    Helper function for specifying extra templates to an ArchiveQuery without any
    parameters (e.g. AllPublicQuery).

    The archive list view for the given query, will look for the following templates

    archives/<model name>/<query_name>/list.html
    archives/<model name>/list.html
    archives/list.html

    and use the first that it finds.
    """
    return [ 'archives/%s/%s/list.html' % ( model._meta.object_name.lower(), query_name ), ]


def param_extra_templates( param=None, selector=None ):
    """
    Helper function for specifying extra templates to an ArchiveQuery, where the query
    takes a single parameter (examples are CategoryQuery or YearQuery).

    The archive list view for the given query, will look for the following templates

    archives/<model name>/<query_name>/list_<stringparam>.html
    archives/<model name>/<query_name>/list.html
    archives/<model name>/list.html
    archives/list.html

    and use the first that it finds.
    """
    if param is None:
        return []

    def func( model, query, query_name, query_data ):

        if param in query_data:
            stringparam = selector( query_data[param], query ) if selector else query_data[param]
            stringparam = str( stringparam )

            return [
                    'archives/%s/%s/list_%s.html' % ( model._meta.object_name.lower(), query_name, stringparam ),
                    'archives/%s/%s/list.html' % ( model._meta.object_name.lower(), query_name ),
                    ]
    return func


# Helper function for specifying extra templates for CategoryQuery.
category_extra_templates = param_extra_templates( param='category', selector=lambda obj, query: getattr( obj, query.url_field ) )

# Helper function for specifying extra templates for YearQuery.
year_extra_templates = param_extra_templates( param='year' )


class AllPublicQuery( ArchiveQuery ):
    """

    """
    def __init__(self, **kwargs):
        defaults = {
                'include_in_urlpatterns': True,
                'url_template': 'djangoplicity.archives.contrib.queries.urls.simple',
                'extra_templates': simple_extra_templates,
                'searchable': True,
            }
        defaults.update( kwargs )
        super(AllPublicQuery, self).__init__( **defaults )

    def queryset( self, model, options, request, **kwargs ):

        now = datetime.now()
        ( qs, args ) = super( AllPublicQuery, self ).queryset( model, options, request, **kwargs )
        qs = self._filter_datetime( qs, now, 'release_date', False, True )
        qs = self._filter_datetime( qs, now, 'embargo_date', False, True )
        qs = qs.filter( published=True )
        return ( qs, args )


class UnpublishedQuery( ArchiveQuery ):
    """

    """

    def __init__(self, **kwargs):
        defaults = {
                'include_in_urlpatterns': True,
                'url_template': 'djangoplicity.archives.contrib.queries.urls.simple',
                'extra_templates': simple_extra_templates,
                'search_default': False,
            }
        defaults.update( kwargs )
        super(UnpublishedQuery, self).__init__( **defaults )

    def queryset( self, model, options, request, **kwargs ):
        ( qs, args ) = super( UnpublishedQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.filter( published=False )
        return ( qs, args )


class EmbargoQuery( ArchiveQuery ):
    """

    """
    def __init__(self, **kwargs):
        defaults = {
                'include_in_urlpatterns': True,
                'url_template': 'djangoplicity.archives.contrib.queries.urls.simple',
                'extra_templates': simple_extra_templates,
                'search_default': False,
            }
        defaults.update( kwargs )
        super(EmbargoQuery, self).__init__( **defaults )

    def queryset( self, model, options, request, **kwargs ):
        now = datetime.now()
        sort_fields = self.sort_fields if self.sort_fields else ( model.Archive.Meta.sort_fields if hasattr( model.Archive.Meta, 'sort_fields') else [] )
        ( qs, args ) = super( EmbargoQuery, self ).queryset( model, options, request, **kwargs )
        qs = self._filter_datetime( qs, now, 'release_date', True, False )
        qs = self._filter_datetime( qs, now, 'embargo_date', False, True )
        qs = qs.filter( published=True )
        # If no sort is defined then sort them by release_date
        if not (request and "sort" in request.GET and sort_fields):
            qs = qs.order_by('release_date')
        return ( qs, args )

    def has_permissions(self, request):
        """ Hook to determine if a request is allowed to view this query. """
        return request.user.is_authenticated


class StagingQuery( ArchiveQuery ):
    """

    """
    def __init__(self, **kwargs):
        defaults = {
                'include_in_urlpatterns': True,
                'url_template': 'djangoplicity.archives.contrib.queries.urls.simple',
                'extra_templates': simple_extra_templates,
                'search_default': False,
            }
        defaults.update( kwargs )
        super(StagingQuery, self).__init__( **defaults )

    def queryset( self, model, options, request, **kwargs ):
        now = datetime.now()
        sort_fields = self.sort_fields if self.sort_fields else ( model.Archive.Meta.sort_fields if hasattr( model.Archive.Meta, 'sort_fields') else [] )
        ( qs, args ) = super( StagingQuery, self ).queryset( model, options, request, **kwargs )
        qs = self._filter_datetime( qs, now, 'embargo_date', True, False )
        qs = qs.filter( published=True )
        # If no sort is defined then sort them by release_date and id
        if not (request and "sort" in request.GET and sort_fields):
            qs = qs.order_by('release_date', model.Archive.Meta.idfield)
        return ( qs, args )

    def has_permissions(self, request):
        """ Hook to determine if a request is allowed to view this query. """
        return request.user.is_superuser or request.user.is_staff


class CategoryQuery( ArchiveQuery ):
    """
    Query for displaying all entries in a certain category.

    Note: by default release/embargo date is not taken into account

    May be defined in an Options class as:

    class Queries(object):
        category = CategoryQuery(
                    relation_field='<category field name>',
                    url_field='<category url field name>',
                    title_field='<category title field name>',
                    browsers=( ... ),
                    verbose_name="..."
                    )

    Keyword argument "relation_field" is the name of the model field in the archive
    model defining the category relationship.

    Keyword argument "url_field" is the name of the model field in the category
    model defining the URL parameter for this category - i.e. if the category query
    is available with the following URL scheme, then "url_field" is the name of the
    model field containing the <url value> values.

        .../archive/category/<url value>/...

    Keyword argument "title_field" is the name of the model field in the category
    model defining the title for the category.

    Keyword argument "use_category_title" determines if the category title should be
    substituted into verbose name. Note title field must exists in category model if
    argument is true.

    All four keyword arguments may be omitted if you use the standard names. In such
    case you models will look like this::

        class SomeCategoryModel( models.Model ):
            name = models.CharField()
            url = models.SlugField()

        class SomeArchive( ArchiveModel, models.Model ):
            ...
            category = models.ManyToManyField( SomeCategoryModel )
    """

    def __init__(self, relation_field=CATEGORY_RELATION_FIELD, url_field=CATEGORY_URL_FIELD, title_field=CATEGORY_TITLE_FIELD, use_category_title=True, featured=None, **kwargs):
        if featured is None:
            featured = []
        if not relation_field:
            raise ImproperlyConfigured( _('Relation field name for category model field must be set.') )
        if not url_field:
            raise ImproperlyConfigured( _('URL field name in category model field must be set.') )

        self.relation_field = relation_field
        self.url_field = url_field
        self.title_field = title_field
        self.use_category_title = use_category_title

        # featured topics
        self.featured = featured

        defaults = { 'include_in_urlpatterns': True, 'url_template': 'djangoplicity.archives.contrib.queries.urls.param', 'extra_templates': category_extra_templates }
        defaults.update( kwargs )
        super(CategoryQuery, self).__init__( **defaults )

    def _get_categorymodel( self, model, name ):
        """
        Find a ManyToManyField or ForeignKey on model with a specific name
        """
        try:
            # First try many to many fields, since there are only normally
            # only few of those.
            field = list(filter( lambda x: x.name == name, model._meta.local_many_to_many ))[0]
        except IndexError:
            # Nothing found so try ForeignKeys
            try:
                field = list(filter( lambda x: x.name == name and isinstance(x, ForeignKey), model._meta.local_fields ))[0]
            except IndexError:
                raise ImproperlyConfigured( 'Relation field does not exist on archive model.' )

        # Both ForeignKey and ManyToManyField defines rel.to for django 1.11 and remote_field.model for django 2+
        import django
        if django.VERSION >= (2, 0):
            return field.remote_field.model
        else:
            return field.rel.to

    def queryset( self, model, options, request, stringparam=None, **kwargs ):
        if not stringparam:
            raise Http404

        #
        # Find category
        #
        categorymodel = self._get_categorymodel( model, self.relation_field )

        try:
            category = categorymodel.objects.get( **{ self.url_field: stringparam } )
            set_manager = getattr( category, "%s_set" % model._meta.model_name )
        except categorymodel.DoesNotExist:
            # URL of non existing category specified.
            raise Http404
        except FieldError:
            raise ImproperlyConfigured( 'URL field does not exist on category model.' )
        except AttributeError:
            raise ImproperlyConfigured( 'Related query set attribute %s_set does not exist on category model.' % model._meta.model_name )

        #if stringparam in self.featured:
        #   print "featured"

        #
        # Select archive items in category
        #
        qs = set_manager.all()

        return ( qs, { 'category': category } )

    def url_args(self, model, options, request, stringparam=None, **kwargs ):
        """
        Hook for query to specify extra reverse URL lookup arguments.
        """
        return [ stringparam ]

    def verbose_name(self, category=None, **kwargs ):
        """
        Method that can be overwritten to customize the archive title.
        """
        try:
            if category and self.use_category_title:
                return _( self._verbose_name ) % getattr( category, self.title_field )
            else:
                return _( self._verbose_name )
        except AttributeError:
            raise ImproperlyConfigured( 'Title field does not exist on category model.')
        except TypeError:
            raise ImproperlyConfigured( 'Title for CategoryQuery does not include substitution string - set "use_category_title" to False or include one and only one %s in the verbose_name.')


class YearQuery( AllPublicQuery ):
    """
    Query for displaying all entries for a certain year

    May be defined in an Options class as:

    class Queries(object):
        year = YearQuery(
                    datetime_feature='release_date',
                    use_year_title=True,
                    browsers=( ... ),
                    verbose_name="..."
                )

    Keyword argument "datetime_feature" is the name of archive datetime feature you
    want to use. Possible values are "release_date", "embargo_date", "created" or
    "last_modified". These must be specified on the archive, e.g.:

    class Model(..):
        ...

        class Archive:
            ...

            class Meta:
                release_date = True


    Keyword argument "use_year_title" determines if the year should be
    substituted into verbose name.
    """

    def __init__(self, datetime_feature='release_date', use_year_title=True, **kwargs):
        self.use_year_title = use_year_title
        self.datetime_feature = datetime_feature

        defaults = { 'include_in_urlpatterns': True, 'url_template': 'djangoplicity.archives.contrib.queries.urls.param', 'extra_templates': year_extra_templates, 'searchable': False }
        defaults.update( kwargs )
        super(YearQuery, self).__init__( **defaults )

    def queryset( self, model, options, request, stringparam=None, **kwargs ):
        if not stringparam:
            raise Http404

        # Convert to year
        try:
            year = int( stringparam )

            # TOOD: Are these constraints really appropriate?
            if year < 1900:
                raise Http404
        except TypeError:
            raise Http404
        except ValueError:
            raise Http404

        (qs, dummy_args) = super( YearQuery, self ).queryset( model, options, request, **kwargs )

        if getattr( qs.model.Archive.Meta, self.datetime_feature, False ):
            fieldname = getattr( qs.model.Archive.Meta, '%s_fieldname' % self.datetime_feature )
            # Check that year is valid:
            # Filter current year
            try:
                qs = qs.filter( Q( **{'%s__gte' % fieldname: datetime(year, 1, 1) } ) & Q( **{'%s__lt' % fieldname: datetime(year + 1, 1, 1) } ) )
            except ValueError:
                # Usually triggered if year is < datetime.MINYEAR or > datetime.MAXYEAR
                raise Http404
            return ( qs, { 'year': year } )
        else:
            raise ImproperlyConfigured( 'The specified datetime feature is not available for the current archive.' )

    def url_args(self, model, options, request, stringparam=None, **kwargs ):
        """
        Hook for query to specify extra reverse URL lookup arguments.
        """
        return [ stringparam ]

    def verbose_name(self, year=None, **kwargs ):
        """
        Method that can be overwritten to customize the archive title.
        """
        try:
            if year and self.use_year_title:
                return _(self._verbose_name) % year
            else:
                return _(self._verbose_name)
        except TypeError:
            raise ImproperlyConfigured( 'Title for YearQuery does not include substitution string - set "use_year_title" to False or include one and only one %d in the verbose_name.')


class FeaturedQuery( AllPublicQuery ):
    """

    """
    def __init__(self, **kwargs):
        defaults = {
                'include_in_urlpatterns': True,
                'url_template': 'djangoplicity.archives.contrib.queries.urls.simple',
                'extra_templates': simple_extra_templates,
                'searchable': True,
            }
        defaults.update( kwargs )
        super( FeaturedQuery, self ).__init__( **defaults )

    def queryset( self, model, options, request, **kwargs ):
        ( qs, args ) = super( FeaturedQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.filter( featured=True )
        return ( qs, args )


class ForeignKeyQuery( AllPublicQuery ):
    """
    Query for retrieving all items related to a specific foreign key.
    """
    def __init__( self, fk_field, *args, **kwargs ):
        self.fk_field = fk_field
        defaults = {
                'include_in_urlpatterns': True,
                'url_template': 'djangoplicity.archives.contrib.queries.urls.param',
                'extra_templates': simple_extra_templates,
                'searchable': True,
            }
        defaults.update( kwargs )
        super( ForeignKeyQuery, self ).__init__( *args, **defaults )

    def queryset( self, model, options, request, stringparam=None, **kwargs ):
        if not stringparam:
            raise Http404

        ( qs, query_data ) = super( ForeignKeyQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.filter( **{ self.fk_field: stringparam } )

        return ( qs, query_data )

    def url_args(self, model, options, request, stringparam=None, **kwargs ):
        """
        Hook for query to specify extra reverse URL lookup arguments.
        """
        return [ stringparam ]


class AdvancedSearchQuery (AllPublicQuery):
    """
    Handles advanced searches.
    """

    #url_include = 'djangoplicity.archives.contrib.search.urls'

    def check_parameters(self, model, options, request):
        """
        Hook to check if parameters (e.g. GET) are neccessary.
        Returns a redirect URL if necessary, or '' if OK
        """
        if not (request.method == 'GET' and request.GET):
            if settings.ENABLE_ADVANCED_SEARCH and hasattr(options, 'AdvancedSearch'):
                if hasattr( options, 'urlname_prefix' ):
                    urlname_prefix = options.urlname_prefix
                    return reverse("%s_%s" % (urlname_prefix, settings.ARCHIVE_URL_SEARCH_PREFIX))

            raise Http404()

    def queryset( self, model, options, request, **kwargs ):

        # get form
        form = AdvancedSearchForm(options, request)

        ( qs, args ) = super( AdvancedSearchQuery, self ).queryset( model, options, request, **kwargs )

        args['search_str_verbose'] = form.repr()

        # Generate the adv_search_str, which is basically the full request
        # string without a few parameters
        get = request.GET.copy()
        for key in ('sort', 'lang'):
            get.pop(key, None)
        args['adv_search_str'] = get.urlencode()

        # do search, filter results
        qs = form.search(qs)

        return ( qs, args )
