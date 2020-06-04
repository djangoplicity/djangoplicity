# -*- coding: utf-8 -*-
#
# djangoplicity-coposweb
# Copyright (c) 2007-2011, European Southern Observatory (ESO)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the European Southern Observatory nor the names
#      of its contributors may be used to endorse or promote products derived
#      from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY ESO ``AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL ESO BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE

"""
Simple wrapper for standard checkout as implemented in payment.views
"""

from django.http import HttpResponseRedirect
from django.views.decorators.cache import never_cache
from livesettings.functions import config_get_group
from payment.views import confirm, payship
from satchmo_store.shop.models import Order
from satchmo_utils.dynamic import lookup_url

coposweb = config_get_group( 'PAYMENT_COPOSWEB' )


def pay_ship_info( request ):
    payment_module = coposweb

    # Copied from payship.base_pay_ship_info
    results = payship.pay_ship_info_verify( request, payment_module )

    if not results[0]:
        return results[1]

    contact = results[1]
    working_cart = results[2]

    # Check if there's anything to pay
    try:
        order = Order.objects.from_request( request )
    except Order.DoesNotExist:
        return HttpResponseRedirect( lookup_url( payment_module, 'satchmo_checkout-step1' ) )

    if order.paid_in_full:
        form_handler = payship.simple_pay_ship_process_form
        template = 'shop/checkout/coposweb/pay_ship_free.html'
    else:
        form_handler = payship.credit_pay_ship_process_form
        template = 'shop/checkout/coposweb/pay_ship.html'

    results = form_handler( request, contact, working_cart, payment_module, allow_skip=False )
    if results[0]:
        return results[1]

    form = results[1]
    return payship.pay_ship_render_form( request, form, template, payment_module, working_cart )
pay_ship_info = never_cache( pay_ship_info )


def confirm_info( request ):
    return confirm.credit_confirm_info( request, coposweb, template='shop/checkout/coposweb/confirm.html' )
confirm_info = never_cache( confirm_info )


def order_csv_file( request, order_id ):
    import warnings
    warnings.warn( "View order_csv_file moved to djangoplicity.archives.contrib.satchmo.views" )
    from djangoplicity.archives.contrib.satchmo.views import order_csv_file as new_order_csv_file
    return new_order_csv_file( request, order_id )
