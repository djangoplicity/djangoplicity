# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

from django.conf.urls import include, url

from djangoplicity.archives.contrib.satchmo.views import order_csv_file, \
    orders_for_category, orders_for_category, orders_for_product, \
    orders_for_product, order_xml_file
from shipping.views import displayDoc

urlpatterns = [
    url( r'^shop/order/(?P<order_id>[0-9]+)/csv/$', order_csv_file, {}, 'satchmo_order_csv_file' ),
    url( r'^shop/order/(?P<order_id>[0-9]+)/xml/$', order_xml_file, {}, 'satchmo_order_xml_file' ),
    url( r'^product/category/(?P<category_id>[0-9]+)/orders/$', orders_for_category, {}, 'satchmo_orders_for_category' ),
    url( r'^product/category/(?P<category_id>[0-9]+)/orders/(?P<format>[a-z]+)/$', orders_for_category, {}, 'satchmo_orders_for_category_fmt' ),
    url( r'^product/product/(?P<product_id>[0-9]+)/orders/$', orders_for_product, {}, 'satchmo_orders_for_product' ),
    url( r'^product/product/(?P<product_id>[0-9]+)/orders/(?P<format>[a-z]+)/$', orders_for_product, {}, 'satchmo_orders_for_product_fmt' ),
    url( r'^print/(?P<doc>[-\w]+)/(?P<id>\d+)', displayDoc, {}, 'satchmo_print_shipping' ),
    url( r'^settings/', include( 'livesettings.urls' ) ),
    url( r'^cache/', include( 'keyedcache.urls' ) ),
]
