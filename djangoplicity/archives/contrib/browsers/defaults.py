# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from django.utils.translation import ugettext_noop as _
from djangoplicity.archives.browsers import ArchiveBrowser
from django.http import Http404, HttpResponse
from djangoplicity.archives.contrib.serialization import Serialization

__all__ = ( 'NormalBrowser', 'ViewAllBrowser', 'ListBrowser', 'SerializationBrowser' )


class NormalBrowser(ArchiveBrowser):
    """ Normal browser showing 6 items at a time. """
    def __init__(self, **kwargs ):
        defaults = { 'verbose_name': _(u'Normal'), 'paginate_by': 6, 'index_template': 'index_normal.html' }
        defaults.update( kwargs )
        super(NormalBrowser, self).__init__( **defaults )


class ViewAllBrowser(ArchiveBrowser):
    def __init__(self, **kwargs ):
        defaults = { 'verbose_name': _(u'View all'), 'paginate_by': 100, 'index_template': 'index_viewall.html' }
        defaults.update( kwargs )
        super(ViewAllBrowser, self).__init__( **defaults )


class ListBrowser(ArchiveBrowser):
    """ Normal browser showing 5 items at a time in a list like fashin. """
    def __init__(self, **kwargs ):
        defaults = { 'verbose_name': _(u'Normal'), 'paginate_by': 20, 'index_template': 'index_list.html' }
        defaults.update( kwargs )
        super(ListBrowser, self).__init__( **defaults )


class SerializationBrowser( ArchiveBrowser ):
    def __init__(self, serializer=None, emitter=None, paginate_by=100, display=False, verbose_name="" ):
        self.serializer = serializer
        self.emitter = emitter
        self._paginate_by = paginate_by
        self.display = display
        self.verbose_name = _(u'Serialization') if not verbose_name else verbose_name
        self.allow_empty = True

    def render( self, request, model, options, query, query_name, qs, query_data, search_str, **kwargs ):
        #
        # Pagination (will evaluate query set)
        #
        try:
            (_paginator, _page_number, page_obj) = self.pagination( options, qs, request, page=kwargs['page'])
        except KeyError:
            raise Http404

        serializer = self.serializer()
        emitter = self.emitter()

        if hasattr( serializer, 'serialize_list' ):
            data = serializer.serialize_list( page_obj.object_list )
        else:
            list_serialization = []
            for obj in page_obj.object_list:
                list_serialization.append( serializer.serialize( obj ).data )
            data = Serialization( list_serialization )

        return emitter.emit( data )

    def response( self, content, **kwargs ):
        return self.emitter().response( HttpResponse( content, content_type=self.emitter.content_type ) )
