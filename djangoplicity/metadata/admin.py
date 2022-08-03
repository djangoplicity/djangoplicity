from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from djangoplicity.metadata.models import TaxonomyHierarchy, SubjectName, Facility, Instrument, Category, Publication, \
    ObservationProposal, TaggingStatus, Program


class TaxonomyHierarchyAdmin( admin.ModelAdmin ):
    list_display = ( 'name', 'avm_code', 'top_level', 'level1', 'level2', 'level3', 'level4', 'level5', )
    list_filter = ( 'top_level', )
    list_display_links = ( 'avm_code', )
    list_editable = ( 'name', 'top_level', 'level1', 'level2', 'level3', 'level4', 'level5', )
    search_fields = ( 'name', )
    fieldsets = (
                    ( None, {'fields': ( 'name', ('top_level', 'level1', 'level2', 'level3', 'level4', 'level5', ) ) } ),
                )
    ordering = ('name',)


class AVMStringListModelAdmin( admin.ModelAdmin ):
    """
    Note intended to be registered in admin.
    """
    list_display = ( 'name', 'simbad_compliant', 'wiki_link' )
    list_filter = ( 'simbad_compliant', )
    search_fields = ( 'name', 'wiki_link' )
    fieldsets = (
                    ( None, {'fields': ( 'name', 'alias', 'simbad_compliant', 'wiki_link' ) } ),
                )
    ordering = ('name',)


class PublishedListModelAdmin( admin.ModelAdmin ):
    list_display = AVMStringListModelAdmin.list_display + ('published',)
    list_filter = AVMStringListModelAdmin.list_filter + ('published',)
    fieldsets = (
                    ( None, {'fields': ( 'name', 'simbad_compliant', 'wiki_link', 'published' ) } ),
                )


class FacilityAdmin( PublishedListModelAdmin ):
    pass


class InstrumentAdmin( PublishedListModelAdmin ):
    pass


class SubjectNameAdmin( AVMStringListModelAdmin ):
    pass


class PublicationAdmin( admin.ModelAdmin ):
    """
    """
    list_display = ( 'bibcode', )
    search_fields = ( 'bibcode', )
    fieldsets = (
                    ( None, {'fields': ( 'bibcode', ) } ),
                )
    ordering = ('-bibcode',)


class ObservationProposalAdmin( admin.ModelAdmin ):
    """
    """
    list_display = ( 'proposal_id', )
    search_fields = ( 'proposal_id', )
    fieldsets = (
                    ( None, {'fields': ( 'proposal_id', ) } ),
                )


class CategoryTypeAdmin( admin.ModelAdmin ):
    list_display = ( 'name', )
    search_fields = ( 'name', )
    fieldsets = (
                    ( None, {'fields': ( 'name', ) } ),
                )


class CategoryAdmin( admin.ModelAdmin ):
    list_display = ( 'url', 'name', 'type', 'enabled', 'logo_url')
    list_editable = ( 'name', )
    list_filter = ( 'type', )
    search_fields = ( 'name', 'url', )
    fieldsets = (
                    ( None, {'fields': ( 'name', 'url', 'type', 'enabled', 'logo_url') } ),
                )


class ProgramAdmin( admin.ModelAdmin ):
    list_display = ( 'url', 'name', 'type', 'logo_url', 'enabled')
    list_editable = ( 'name', )
    list_filter = ( 'type', )
    search_fields = ( 'name', 'url', )
    fieldsets = (
                    ( None, {'fields': ( 'name', 'url', 'type', 'enabled' ,'logo_url') } ),
                )

class TaggingStatusAdmin( admin.ModelAdmin ):
    list_display = ( 'slug', 'name',)
    list_editable = ( 'name', )
    search_fields = ( 'slug', 'name', )
    fieldsets = (
                    ( None, {'fields': ( 'slug', 'name', ) } ),
                )
    ordering = ( 'name', )


def register_with_admin( admin_site ):
    admin_site.register( TaxonomyHierarchy, TaxonomyHierarchyAdmin )
    admin_site.register( SubjectName, SubjectNameAdmin )
    admin_site.register( Facility, FacilityAdmin )
    admin_site.register( Instrument, InstrumentAdmin )
    admin_site.register( Category, CategoryAdmin )
    admin_site.register( Program, ProgramAdmin )
    admin_site.register( Publication, PublicationAdmin )
    admin_site.register( ObservationProposal, ObservationProposalAdmin )
    admin_site.register( TaggingStatus, TaggingStatusAdmin )

# Register with default admin site
register_with_admin( admin.site )
