# -*- coding: utf-8 -*-
#
# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

from builtins import str
from datetime import datetime

from django.http import HttpResponse, HttpResponseForbidden
from django.utils.translation import ugettext_lazy as _
from djangoplicity.archives.contrib.satchmo.export import factory

from satchmo_store.shop.models import Config
from satchmo_store.shop.admin import ConfigOptions


def satchmo_admin( shop_site ):
    from satchmo_store.shop.models import Order
    from django.contrib import admin
    old_site = admin.site
    admin.site = shop_site

    # These imported modules must be left to appear in the shop interface
    import l10n.admin
    import payment.admin
    #import payment.modules.giftcertificate.admin
    #import payment.modules.purchaseorder.admin
    import product.admin
    #import product.modules.configurable.admin
    #import product.modules.custom.admin
    #import product.modules.downloadable.admin
    #import product.modules.subscription.admin
    #import product.templatetags.satchmo_product_admin
    #import satchmo_ext.brand.admin
    #import satchmo_ext.newsletter.admin
    #import satchmo_ext.tieredpricing.admin
    #import satchmo_ext.upsell.admin
    #import satchmo_ext.wishlist.admin
    import satchmo_store.contact.admin
    #import satchmo_store.contact.supplier.admin
    import satchmo_store.shop.admin
    import satchmo_utils.admin
    #import shipping.modules.productshipping.admin
    #import shipping.modules.tiered.admin
    #import shipping.modules.tieredquantity.admin
    import shipping.modules.tieredweight.admin
    #import tax.modules.area.admin
    #import tax.modules.us_sst.admin

    #
    # Extend satchmo order admin
    #
    class ExtendedOrderOptions( satchmo_store.shop.admin.OrderOptions ):
        actions = ['action_export', 'action_export_xml', 'action_status_temp', 'action_status_blocked', 'action_status_in_process', 'action_status_billed',
                'action_status_shipped', 'action_status_complete', 'action_status_cancelled']

        def action_export( self, request, queryset, exporter=None ):
            if not request.user.has_perm('shop.change_order'):
                return HttpResponseForbidden()

            dt = datetime.now()

            response = HttpResponse( content_type="text/plain" )
            response['Content-Disposition'] = "attachment; filename=webshop-%.2d%.2d%.2d_%.2dh%.2dm.%s" % ( dt.year, dt.month, dt.day, dt.hour, dt.minute, exporter if exporter is not None else 'csv' )

            if exporter is None:
                exporter = factory.create_default( response )
            else:
                exporter = factory.create( exporter, response )

            # Don't import orders without statuses (i.e.: not paid)
            queryset = queryset.exclude(status='')

            exporter.export( queryset )

            return response
        action_export.short_description = _( "Export orders" )

        def action_export_xml( self, request, queryset ):
            return self.action_export( request, queryset, exporter='xml' )
        action_export_xml.short_description = _( "Export orders (XML)" )

        def action_change_status( self, request, queryset, new_status=None ):
            """
            Bulk change of order status.
            """
            if not request.user.has_perm('shop.change_order'):
                return HttpResponseForbidden()

            from satchmo_store.shop.models import ORDER_STATUS
            if new_status not in [x[0] for x in ORDER_STATUS]:
                return

            username = request.user.username if request.user.is_authenticated else 'N/A'

            orderids = []

            for obj in queryset:
                orderids.append( str(obj.id) )
                obj.add_status( status=new_status, notes='Bulk status change by %s' % username )

            self.message_user( request, "Order status set to %s for orders %s." % ( new_status.lower(), ", ".join(orderids) ) )

        def action_status_temp( self, request, queryset ):
            return self.action_change_status( request, queryset, new_status='Temp' )
        action_status_temp.short_description = _( "Set Temp" )

        def action_status_blocked( self, request, queryset ):
            return self.action_change_status( request, queryset, new_status='Blocked' )
        action_status_blocked.short_description = _( "Set Blocked" )

        def action_status_in_process( self, request, queryset ):
            return self.action_change_status( request, queryset, new_status='In Process' )
        action_status_in_process.short_description = _( "Set In Process" )

        def action_status_billed( self, request, queryset ):
            return self.action_change_status( request, queryset, new_status='Billed' )
        action_status_billed.short_description = _( "Set Billed" )

        def action_status_shipped( self, request, queryset ):
            return self.action_change_status( request, queryset, new_status='Shipped' )
        action_status_shipped.short_description = _( "Set Shipped" )

        def action_status_complete( self, request, queryset ):
            return self.action_change_status( request, queryset, new_status='Complete' )
        action_status_complete.short_description = _( "Set Complete" )

        def action_status_cancelled( self, request, queryset ):
            return self.action_change_status( request, queryset, new_status='Cancelled' )
        action_status_cancelled.short_description = _( "Set Cancelled" )

    try:
        admin.site.unregister( Order )
    except admin.sites.NotRegistered:
        pass

    admin.site.register( Order, ExtendedOrderOptions )
    admin.site.register(Config, ConfigOptions)

    #
    # Hack: Fix shipping label link, by replacing function
    #

    shop_site = admin.site
    admin.site = old_site
    return shop_site
