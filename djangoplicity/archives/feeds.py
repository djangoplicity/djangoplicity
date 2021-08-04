# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
"""
Djangoplicity Archive Feeds

Provides configuration, display and setup of RSS Feeds for Djangoplicity Archives.
"""

from builtins import object
from django.conf.urls import url
from django.contrib.sites.models import Site
from django.core.cache import cache

from django.http import Http404
from djangoplicity.feeds import conf as feedsconf
from djangoplicity.feeds.feeds import DjangoplicityFeed

FORMATS = feedsconf.get_formats() if feedsconf.get_formats() else {}


from django.urls import reverse



class DjangoplicityArchiveFeed( DjangoplicityFeed ):
    """
    Base class for Archive RSS Feeds. Its subclasses must be instantiated, but not itself.

    This class is in need of some restructuring as it was coded before Django 1.2 when
    the Syndication framework received a major overhaul. In general it is too complex
    and without clear responsibilities.

    Examples: This class should not know anything about 'top100', 'category' or similar
    This should be located in subclasses.

    What can be done:
     1) One class that supports a basic feed based on a single archive query
     2) A more advanced feed class that supports e.g urls parameters
    """
    category = None
    format = None
    override_guids = {}

    class Meta( object ):
        model = None
        options = None
        latest_fieldname = None
        enclosure_resources = { '': None }
        default_query = None
        category_query = None
        items_to_display = 25
        external_feed_url = None
        include_unpublished = False

    def __init__( self, *args, **kwargs ):
        if not self.Meta.model and \
            self.Meta.latest_fieldname and \
            self.Meta.enclosure_resources and \
            self.Meta.default_query:
            raise Exception( "DjangoplicityArchiveFeed should not be instantiated, but inherited by subclasses" )
        else:
            super( DjangoplicityArchiveFeed, self ).__init__( *args, **kwargs )

    def __call__( self, request, *args, **kwargs ):
        """
        Added support for caching an RSS feed (used for the VAMP feed which is expensive to generate)
        """
        response = None
        if hasattr( self.Meta, 'cache' ):
            key = "djangoplicity_feed_%s" % kwargs.get( 'name', 'default' )
            response = cache.get( key )

        if not response:
            response = super( DjangoplicityArchiveFeed, self ).__call__( request, *args, **kwargs )
            if hasattr( self.Meta, 'cache' ):
                cache.set( key, response, self.Meta.cache )

        return response

    @classmethod
    def get_feed_urls( cls, name='', url_prefix='', name_prefix=None ):
        """
        Method for generating URL patterns for this feed.

        See djangoplicity.archives.urls for general about archive URL generation.
        """
        #reverse_name = "%s_%s" % ( name_prefix, name ) if name else name_prefix
        reverse_name = name_prefix

        if name == "category":
            # e.g .../feed/category/esocast/ and .../feed/category/esocast/sd/
            urlpatterns = [url( r'^%s/category/(?P<category_name>[-_\w]+)/((?P<format>[-_\w]+)/)?$' % url_prefix, cls(), name=reverse_name, kwargs={ 'name': 'category' } )]
        elif name:
            # e.g .../feed/ or .../feed/top100/
            urlpatterns = [ url( r'^%s/(?P<name>%s)/$' % ( url_prefix, name ), cls(), name=reverse_name )]
        else:
            urlpatterns = [ url( r'^%s/$' % url_prefix, cls(), name=reverse_name, kwargs={ 'name': 'default' } )]

        return urlpatterns

    @classmethod
    def archive_feed_url( cls, name=None, stringparam=None, lang=None, reverse_func=None, **kwargs ):
        """
        Get the main URL for this feed.
        """
        # category
        if name == 'category' and stringparam:
            feed_url = feedsconf.get_by_category( stringparam, 'external_feed_url', None )

            if feed_url:
                return feed_url
            else:
                return reverse( '%s_feed' % cls.Meta.options.urlname_prefix, kwargs={ 'category_name': stringparam } )

        elif lang and lang != 'en' and name == 'default' and reverse_func:
            return reverse_func( '%s_feed' % cls.Meta.options.urlname_prefix, lang=lang )
        elif name and not stringparam and name != 'default':
            return reverse( '%s_feed' % cls.Meta.options.urlname_prefix, kwargs={ 'name': name } )
        elif hasattr( cls.Meta, 'external_feed_url' ) and cls.Meta.external_feed_url:
            return cls.Meta.external_feed_url
        elif name == 'default':
            return reverse( '%s_feed' % cls.Meta.options.urlname_prefix )

    def item_pubdate( self, item ):
        """
        Takes an news item, as returned by items(), and returns the news'
        release date.
        """
        return getattr( item, self.Meta.latest_fieldname )

    def items( self, obj ):
        """
        Returns the feed's items based on the obj returned by get_object
        """
        if not obj:  # no URL parameters
            qs, _b = self.Meta.default_query.queryset( self.Meta.model, self.Meta.options, None )
            if not self.Meta.include_unpublished and self.Meta.model.Archive.Meta.published:
                qs = qs.filter( published=True )
            return qs.order_by( '-' + self.Meta.latest_fieldname )[:self.Meta.items_to_display]

        else:  # category feed
            qs, _b = self.Meta.category_query.queryset( self.Meta.model, self.Meta.options, None, stringparam=self.category )
            if not self.Meta.include_unpublished and self.Meta.model.Archive.Meta.published:
                qs = qs.filter( published=True )
            return qs.order_by( '-' + self.Meta.latest_fieldname )[:self.Meta.items_to_display]

    def _get_resource( self, item ):
        """
        Returns the appropriate resource according to format and item.
        """
        resource_name = None
        resource = None

        if self.format:
            resource_name = self.Meta.enclosure_resources.get( self.format, None )

        # Fall back to default resource
        if not resource_name:
            resource_name = self.Meta.enclosure_resources.get( '', None )

        if resource_name:
            # For historic/migration reasons, values in FeedSettings.enclosure_resources dict
            # can be both strings and lists, so make sure we only have a list to work with.
            #
            # During re-encoding of videos, this allows to serve vodcast feeds from multiple
            # formats.
            if not isinstance( resource_name, list ):
                resource_name = [resource_name]

            # Find first available resource
            for r in resource_name:
                if hasattr( item, r ):
                    resource = getattr( item, r )
                    if resource:
                        # Resource is none, if no file exists for the resource, so
                        # continue loop until a valid resource is found.
                        break

        return resource

    def item_enclosure_url( self, item ):
        """
        Returns the appropriate enclosure URL according to specified format (or defaults to '' in enclosure_resources)
        """
        file = self._get_resource( item )
        if file:
            return file.absolute_url
        return None

    def item_enclosure_length( self, item ):
        """
        File size of meia enclosure
        """
        file = self._get_resource( item )
        if file:
            size = int( file.size )
            if not file.closed:
                file.close()
            return size
        else:
            return 0

    def item_enclosure_mime_type( self, item ):
        if hasattr( self.Meta, 'enclosure_mimetype' ):
            return self.Meta.enclosure_mimetype
        else:
            return 'image/jpeg'

    def get_object( self, request, *args, **kwargs ):
        """
        Please see django.contrib.syndication.views.Feed.__call__() for how this method is
        integrated into the Feed class.
        """
        # See get_feed_urls() where the name parameter is specified.
        if 'category_name' not in kwargs:
            return None

        # test for category format in URL
        try:
            self.category = kwargs['category_name']
            self.title = feedsconf.get_by_category( self.category, 'title', None )
            self.link = feedsconf.get_by_category( self.category, 'link', self.link )
            self.description = feedsconf.get_by_category( self.category, 'description', self.description )
            self.header_template = feedsconf.get_by_category( self.category, 'header_template', None )
            self.author = feedsconf.get_by_category( self.category, 'author', None )
            self.title_template = feedsconf.get_by_category( self.category, 'title_template', self.title_template if hasattr( self, 'title_template' ) else None )
            self.description_template = feedsconf.get_by_category( self.category, 'description_template', self.description_template )
        except IndexError:
            raise Http404

        try:
            self.format = kwargs.get( 'format' )

            # Format = None, means it wasn't specified via the URL (hence set it to default which is empty string).
            if self.format is None:
                self.format = ''

            if self.format not in FORMATS:
                raise Http404
        except IndexError:
            raise Http404

        if not self.title:
            try:
                self.qs, b = self.Meta.category_query.queryset( self.Meta.model, self.Meta.options, None, stringparam=self.category )
                newtitle = self.Meta.category_query.verbose_name( **b )
            except Exception:
                newtitle = self.title

            self.title = newtitle

        try:
            # basic repr
            repr, _custom_header = FORMATS.get( self.format, self.format )
            self.title = self.title % repr
        except TypeError:
            pass

        return self.category, self.format

    def item_guid( self, obj ):
        """
        Provides legacy guid compatibility, falls back to absolute URL

        This is especially important for podcast feeds where e.g. iTunes
        will think that an episode with a changed guid is a new episode
        and start downloading it (i.e lots of traffic on your static server
        and irritation for your users).
        """
        guids = self.override_guids
        if self.format and hasattr( self, 'override_guids_format' ):
            guids = self.override_guids_format.get( self.format, guids )
        return guids.get( obj.pk, "https://%s%s" % ( Site.objects.get_current().domain, obj.get_absolute_url() ) )
