# -*- coding: utf-8 -*-
#
# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

"""
"""

from djangoplicity.contrib import admin as dpadmin
from djangoplicity.archives.contrib.satchmo.freeorder.models import FreeOrder
from django.utils.translation import ugettext_lazy as _


class FreeOrderAdmin( dpadmin.DjangoplicityModelAdmin ):
    list_display = ( 'name', 'email', 'country', 'accepted', 'submitted', 'reviewed', 'discount_code' )
    list_filter = ( 'accepted', 'country')
    search_fields = ( 'name', 'email', 'justification', 'discount_code' )
    fieldsets = (
                    ( 'Application', {'fields': ( 'name', 'email', 'country', 'justification'), } ),
                    ( 'Review', {'fields': ( 'accepted', 'reject_reason', 'reviewed' ), } ),
                    ( 'Discount Code', {'fields': ('discount_code', ), }),
                )
    ordering = ('-submitted', )
    readonly_fields = ['reviewed', 'discount_code']
    actions = ['action_accept', 'action_reject_noreason', 'action_reject_nostock', 'action_reject_unqualified', 'action_update_accepted']

    def action_update_accepted( self, request, objects ):
        for obj in objects:
            if obj.accepted:
                obj.rebuild_free_products()
        self.message_user( request, _( "Selected free order applications were updated" ) )
    action_update_accepted.short_description = _("Update accepted free order applications")

    def action_accept( self, request, objects ):
        for obj in objects:
            obj.accepted = True
            obj.save()
        self.message_user( request, _( "Selected free order applications were accepted" ) )
    action_accept.short_description = _("Accept selected free order applications")

    def action_reject_noreason( self, request, objects ):
        for obj in objects:
            obj.accepted = False
            obj.save()
        self.message_user( request, _( "Selected free order applications were rejected (no reason)" ) )
    action_reject_noreason.short_description = _("Reject selected free order applications (no reason)")

    def action_reject_nostock( self, request, objects ):
        for obj in objects:
            obj.accepted = False
            obj.reject_reason = 'NOSTOCK'
            obj.save()
        self.message_user( request, _( "Selected free order applications were rejected (no stock)" ) )
    action_reject_nostock.short_description = _("Reject selected free order applications (no stock)")

    def action_reject_unqualified( self, request, objects ):
        for obj in objects:
            obj.accepted = False
            obj.reject_reason = 'UNQUALIFIED'
            obj.save()
        self.message_user( request, _( "Selected free order applications were rejected (unqualified)" ) )
    action_reject_unqualified.short_description = _("Reject selected free order applications (unqualified)")

    def action_reject_insufficient( self, request, objects ):
        for obj in objects:
            obj.accepted = False
            obj.reject_reason = 'INSUFFICIENT'
            obj.save()
        self.message_user( request, _( "Selected free order applications were rejected (insufficient)" ) )
    action_reject_unqualified.short_description = _("Reject selected free order applications (insufficient)")


def register_with_admin( admin_site ):
    admin_site.register( FreeOrder, FreeOrderAdmin )
