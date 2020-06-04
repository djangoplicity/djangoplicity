# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from django_ace import AceWidget

from django import forms
from django.contrib import admin

from djangoplicity.reports.models import Report, ReportGroup


class ReportAdvancedForm(forms.ModelForm):
    sql_command = forms.CharField(widget=AceWidget(mode='pgsql', width='100%'))


class ReportGroupAdmin( admin.ModelAdmin ):
    list_display = ( 'name', )
    search_fields = ( 'name', )
    ordering = ( 'name', )


class ReportAdvancedAdmin( admin.ModelAdmin ):
    list_display = ( 'id', 'name', 'group', 'description', 'is_mailable' )
    list_display_links = ('id', 'name')
    search_fields = ( 'name', 'description' )
    ordering = ( 'name', )
    list_filter = ( 'group', )
    form = ReportAdvancedForm
    fieldsets = (
    ( 'Details',
        {'fields': ( 'name', 'group', 'description', 'is_mailable' )} ),
    ( 'SQL Command',
        {'fields': ( 'displayed_fields', 'sql_command' ) }),

    )


class ReportAdmin( admin.ModelAdmin ):
    list_display = ( 'pk', 'name', 'group', 'description', 'is_mailable' )
    list_display_links = ('pk', 'name')
    search_fields = ( 'name', 'description' )
    ordering = ( 'name', )
    list_filter = ( 'group', )
    fieldsets = (
    ( 'Details',
        {'fields': ( 'name', 'group', 'description', 'is_mailable' )}),
    )


def register_with_admin( admin_site ):
    admin_site.register( Report, ReportAdmin )
    admin_site.register( ReportGroup, ReportGroupAdmin )


def advanced_register_with_admin( admin_site ):
    admin_site.register( Report, ReportAdvancedAdmin )
    admin_site.register( ReportGroup, ReportGroupAdmin )

# Register with default admin site
register_with_admin( admin.site )
