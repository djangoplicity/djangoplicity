from djangoplicity.archives.contrib.queries import AllPublicQuery, FeaturedQuery
from djangoplicity.metadata.archives.queries import ProgramPublicQuery

class AnnouncementsAllPublicQuery(AllPublicQuery):
    '''
    Query to hide is_e_and_e announcements
    '''
    def queryset(self, model, options, request, **kwargs):
        (qs, query_data) = super(AnnouncementsAllPublicQuery, self).queryset(model, options, request, **kwargs)
        qs = qs.filter(is_e_and_e=False)
        return (qs, query_data)
    

class AnnouncementsEAndEQuery(AllPublicQuery):
    '''
    Query to hide is_e_and_e announcements
    '''
    def queryset(self, model, options, request, **kwargs):
        (qs, query_data) = super(AnnouncementsEAndEQuery, self).queryset(model, options, request, **kwargs)
        qs = qs.filter(is_e_and_e=True)
        return (qs, query_data)


class AnnouncementsFeaturedQuery(FeaturedQuery):
    '''
    Query to hide is_e_and_e announcements
    '''
    def queryset(self, model, options, request, **kwargs):
        (qs, query_data) = super(AnnouncementsFeaturedQuery, self).queryset(model, options, request, **kwargs)
        qs = qs.filter(is_e_and_e=False)
        return (qs, query_data)
    

class AnnouncementsProgramsQuery(ProgramPublicQuery):
    '''
    Query to hide is_e_and_e announcements
    '''
    def queryset(self, model, options, request, **kwargs):
        (qs, query_data) = super(AnnouncementsProgramsQuery, self).queryset(model, options, request, **kwargs)
        qs = qs.filter(is_e_and_e=False)
        return (qs, query_data)
