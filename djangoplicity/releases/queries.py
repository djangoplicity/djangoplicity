from datetime import datetime

from djangoplicity.metadata.archives.queries import WebCategoryQuery


class WebCategoryPublicQuery(WebCategoryQuery):
    """
    Query for public images in a certain category, which takes into account that an
    image can be bound by its release.
    """
    def queryset( self, model, options, request, **kwargs ):
        now = datetime.now()
        ( qs, query_data ) = super( WebCategoryPublicQuery, self ).queryset( model, options, request, **kwargs )
        qs = self._filter_datetime( qs, now, 'release_date', False, True )
        qs = self._filter_datetime( qs, now, 'embargo_date', False, True )
        qs = qs.filter( published=True )
        return ( qs, query_data )
