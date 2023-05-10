# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from builtins import object
from django.contrib import admin
from django.core.cache import cache
from django.db import models

from djangoplicity.contrib.admin.widgets import HierarchicalSelect, AdminRichTextAreaWidget, LinkWidget



class DjangoplicityModelAdmin( admin.ModelAdmin ):
    """
    Extended version of the Django provided ModelAdmin from newforms-admin.
    This extended model admin adds features for
     * defining richtext editors for specific textarea fields (or all textarea fields if needed).
     * a foreign key selector for django-mptt models that show the tree structure

    Usage::

    class ModelOptions( djangoplicity.contrib.admin.options.DjangoplicityModelAdmin ):
        fieldsets = ...
        richtext_fields = ( '<textfield1>', '<textfield2>', ... )

    class MPTTModelOptions( djangoplicity.contrib.admin.options.DjangoplicityModelAdmin ):
        fieldsets = ...
        mptt_tree_foreign_key = True

        # Uncommment following if you explicitly changed the name of the parent model field
        # mptt_tree_parent_name = '<new parent name>'
    """

    # Name of the parent_attr in Django MPTT model. A django-mptt model has a parent field defined
    # such as:
    #
    #    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')

    # In case the name of the field is not 'parent' (which explicitly require you to specify the parent_attr
    # in the model), you will need to change this attribute as well to the same value as parent_attr. Hence, something
    # like

    # class MPTTModel( ... )
    #   mptt_tree_parent_name = '<value of parent_atrr>'
    #   mptt_tree_foreign_key = True
    mptt_tree_parent_name = 'parent'

    # Set to true to enable hierarchical select of parent.
    mptt_tree_foreign_key = False

    richtext_fields = ()
    link_fields = ()

    # Define a list of TextField names, which should be edited with the a RichText editor.

    def formfield_for_dbfield( self, db_field, **kwargs ):
        """
        Hook for specifying the form Field instance for a given database Field
        instance.

        See also django.contrib.admin.options.BaseModelAdmin.formfield_for_dbfield
        """
        request = kwargs.pop( "request", None )

        # For ForeignKey - Django MPTT parent widget
        if self.mptt_tree_foreign_key:
            # Change the widget used for a ForeignKey with field name parent.
            if isinstance( db_field, models.ForeignKey ) and db_field.name == self.mptt_tree_parent_name:
                kwargs['widget'] = HierarchicalSelect()

        # For TextFields, add a custom CSS class and JavaScript.
        if self.richtext_fields:
            if isinstance( db_field, models.TextField ) and db_field.name in self.richtext_fields:
                kwargs['widget'] = AdminRichTextAreaWidget()
                return db_field.formfield( **kwargs )

        # For LinkFields, add a custom class
        if self.link_fields:
            if isinstance( db_field, models.CharField ) and db_field.name in self.link_fields:
                kwargs['widget'] = LinkWidget()
                return db_field.formfield( **kwargs )

        kwargs.update(  { "request": request } )
        return super( DjangoplicityModelAdmin, self ).formfield_for_dbfield( db_field, **kwargs )

    class Media:
        # Javascript to collapse filter pane in admin
        js = ['djangoplicity/js/list_filter_collapse.js']


def invalidate_cache( f ):
    """
    decorator used to wrap around function methods in order to invalidate 1 or more cache keys once they run
    """
    def new( self, *args, **kwargs ):
        ret = f( self, *args, **kwargs )
        keys = getattr( self, 'cache_keys' )
        if keys:
            for key in keys:
                cache.delete( key )
        return ret
    return new


class CacheInvalidator( object ):
#   base_class = DjangoplicityModelAdmin
    cache_keys = ()

    @invalidate_cache
    def save_form( self, *args, **kwargs ):
        return super( CacheInvalidator, self ).save_form( *args, **kwargs )

    @invalidate_cache
    def save_model( self, *args, **kwargs ):
        return super( CacheInvalidator, self ).save_model( *args, **kwargs )

    @invalidate_cache
    def save_formset( self, *args, **kwargs ):
        return super( CacheInvalidator, self ).save_formset( *args, **kwargs )

    @invalidate_cache
    def delete_view( self, *args, **kwargs ):
        return super( CacheInvalidator, self ).delete_view( *args, **kwargs )
