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

from builtins import str
import csv

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_text
from djangoplicity.archives.contrib.satchmo.export import factory
from product import views
from product.models import Product, Category
from satchmo_store.shop.models import Order
from satchmo_store.shop.views.home import home

satchmo_category_view = views.category_view


from django.urls import reverse


def not_found_view( request, *args, **kwargs ):
    raise Http404


def category_view( request, slug, parent_slugs='', template='product/category.html' ):
    """
    Wrapper around the Satchmo category view which ensures that each category can have it's
    own template.
    """
    if slug != 'index':
        templates = [ 'product/category_%s.html' % slug, template ]
    else:
        templates = template

    # Note the argument 'tempalte' is passed directly to render in satchmo_category_view.
    # Thus we can give a list of templates instead.
    return satchmo_category_view( request, slug, parent_slugs=parent_slugs, template=templates )


# Override satchmo category view.
views.category_view = category_view


@login_required
@staff_member_required
@permission_required("shop.change_order" )
def order_csv_file( request, order_id ):
    # Wed Oct 23 11:03:51 CEST 2013 - Mathias
    # This actually returns a xml file as it's the default in export.py
    # so even though it's refered to as a CSV file everywhere it seems
    # that Navision does expect a XML.
    # In the future this should be cleaned up to prevent confusion...
    return _order_file( request, order_id )


@login_required
@staff_member_required
@permission_required("shop.change_order" )
def order_xml_file( request, order_id ):
    return _order_file( request, order_id, exporter_type='xml' )


def _order_file( request, order_id, exporter_type=None ):
    """
    Generate CSV file to be imported by Navision.
    """
    try:
        order = Order.objects.get( id__exact=order_id )
    except Order.DoesNotExist:
        raise Http404

    try:
        orderno = order.get_variable("ORDER_ID").value
    except AttributeError:
        raise Http404

    response = HttpResponse( content_type="text/plain" )
    response['Content-Disposition'] = "attachment; filename=%s.%s" % ( orderno, exporter_type if exporter_type is not None else 'csv' )

    if exporter_type is None:
        exporter = factory.create_default( response )
    else:
        exporter = factory.create( exporter_type, response )

    exporter.export( [order] )

    return response


def _get_product_orders(product_id):
    """ Get all product orders associated with a product """
    p = Product.objects.get(pk=product_id)
    orders = Order.objects.filter(orderitem__product=p).select_related('contact').exclude(status='')

    # Conferences are ordered by last name, other by timestamp
    if p.category.filter(parent__name='Conferences'):
        orders = orders.order_by('contact__last_name')
    else:
        orders = orders.order_by('-time_stamp')

    return (p, orders)


@login_required
@staff_member_required
@permission_required("shop.change_order" )
def orders_for_product( request, product_id, format=None, **kwargs ):
    """
    """
    from satchmo_utils.numbers import round_decimal
    try:
        ( product, orders ) = _get_product_orders( int( product_id ) )
    except ( ValueError, Product.DoesNotExist ):
        raise Http404

    header = [
        "",
        "Order no.",
        "Status",
        "ID",
        "Invoice",
        "Last name",
        "First name",
        "Email",
        "Timestamp",
        "Qty",
        "Total",
        "Discount code",
        "Shipping addressee",
        "Shipping street 1",
        "Shipping street 2",
        "Shipping city",
        "Shipping state",
        "Shipping postal code",
        "Shipping country",
        "Billing addressee",
        "Billing street 1",
        "Billing street 2",
        "Billing city",
        "Billing state",
        "Billing postal code",
        "Billing country",
    ]

    def _round( val, places=2 ):
        return str( round_decimal( val=val, places=places, normalize=False ) )

    table = []

    total_sold = 0

    n = 0
    for n, o in enumerate(orders):
        qty = 0
        for i in o.orderitem_set.filter( product=product ):
            qty += i.quantity

        try:
            order_id = o.get_variable( "ORDER_ID" ).value
        except AttributeError:
            order_id = 'unknown'

        row = [
            n + 1,
            order_id,
            o.status,
            o.id,
            '<a href="%s">invoice</a>' % reverse('satchmo_print_shipping', None, None, {'doc': 'invoice', 'id': o.id}),
            o.contact.last_name,
            o.contact.first_name,
            o.contact.email,
            str(o.time_stamp),
            _round( qty, places=0 ),
            _round(o.total),
            o.discount_code,
            o.ship_addressee,
            o.ship_street1,
            o.ship_street2,
            o.ship_city,
            o.ship_state,
            o.ship_postal_code,
            o.ship_country,
            o.bill_addressee,
            o.bill_street1,
            o.bill_street2,
            o.bill_city,
            o.bill_state,
            o.bill_postal_code,
            o.bill_country,
        ]
        table.append( row )

        total_sold += qty

    if format is None or format == 'html':
        opts = Product._meta
        app_label = opts.app_label

        context = {
            "object_name": force_text( opts.verbose_name ),
            'objects': table,
            'header': header,
            'product': product,
            "opts": opts,
            "app_label": app_label,
            "total_sold": total_sold,
        }
        return render(request, "admin/%s/%s/%s" % ( app_label, opts.object_name.lower(), "orders_for_product.html" ), context)
    elif format == 'csv':
        response = HttpResponse( content_type="text/plain" )
        response['Content-Disposition'] = "attachment; filename=%s.txt" % product.slug
        writer = csv.writer( response )
        header = [str( x ).encode( 'utf8', 'replace' ) for x in header]
        writer.writerow( header )

        for row in table:
            row = [str( x ).encode( 'utf8', 'replace' ) for x in row]
            writer.writerow( row )
        return response
    else:
        raise Http404


@login_required
@staff_member_required
@permission_required("shop.change_order" )
def orders_for_category( request, category_id, format=None, **kwargs ):
    """
    """
    from satchmo_utils.numbers import round_decimal

    try:
        category = Category.objects.get(pk=category_id)
        orders = Order.objects.filter( orderitem__product__category=category ).exclude( status='' ).order_by('-pk').distinct()
    except ( ValueError, Product.DoesNotExists ):
        raise Http404

    header = [
        "",
        "Order no.",
        "Status",
        "ID",
        "Product ID",
        "Last name",
        "First name",
        "Email",
        "Timestamp",
        "Qty",
        "Total",
        "Discount code",
        "Shipping addressee",
        "Shipping street 1",
        "Shipping street 2",
        "Shipping city",
        "Shipping state",
        "Shipping postal code",
        "Shipping country",
        "Billing addressee",
        "Billing street 1",
        "Billing street 2",
        "Billing city",
        "Billing state",
        "Billing postal code",
        "Billing country",
    ]

    def _round( val, places=2 ):
        return str( round_decimal( val=val, places=places, normalize=False ) )

    table = []

    total_sold = 0
    n = 0

    for o in orders:
        qty = 0
        for product in [i.product for i in o.orderitem_set.filter(product__category=category)]:

            for i in o.orderitem_set.filter( product=product ):
                qty += i.quantity

            try:
                order_id = o.get_variable( "ORDER_ID" ).value
            except AttributeError:
                order_id = 'unknown'

            row = [
                n + 1,
                '<a href="%s">%s</a>' % (reverse('adminshop_site:shop_order_change', args=[o.id]), order_id),
                o.status,
                o.id,
                product.sku,
                o.contact.last_name,
                o.contact.first_name,
                o.contact.email,
                str(o.time_stamp),
                _round( qty, places=0 ),
                _round(o.total),
                o.discount_code,
                o.ship_addressee,
                o.ship_street1,
                o.ship_street2,
                o.ship_city,
                o.ship_state,
                o.ship_postal_code,
                o.ship_country,
                o.bill_addressee,
                o.bill_street1,
                o.bill_street2,
                o.bill_city,
                o.bill_state,
                o.bill_postal_code,
                o.bill_country,
            ]
            table.append( row )
            n += 1

        total_sold += qty

    if format is None or format == 'html':
        opts = Category._meta
        app_label = opts.app_label

        context = {
            "object_name": force_text( opts.verbose_name ),
            'objects': table,
            'header': header,
            'category': category,
            "opts": opts,
            "app_label": app_label,
            "total_sold": total_sold,
        }
        return render(request, "admin/%s/%s/%s" % ( app_label, opts.object_name.lower(), "orders_for_category.html" ), context)
    elif format == 'csv':
        response = HttpResponse( content_type="text/plain" )
        response['Content-Disposition'] = "attachment; filename=%s.txt" % category.slug
        writer = csv.writer( response )
        header = [str( x ).encode( 'utf8', 'replace' ) for x in header]
        writer.writerow( header )

        for row in table:
            row = [str( x ).encode( 'utf8', 'replace' ) for x in row]
            writer.writerow( row )
        return response
    else:
        raise Http404


def fb_home(request):
    return home(request, template="shop/fb_index.html")
