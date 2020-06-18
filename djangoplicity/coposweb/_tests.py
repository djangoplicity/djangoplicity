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

from django.core import urlresolvers
from django.test import TestCase
from django.test.client import Client
from djangoplicity.coposweb import CoposWebManager
from livesettings.functions import config_get, config_get_group
import keyedcache
import unittest
import random

manager = CoposWebManager( user="", password="", url="https://coposweb.companydirect.de/posh/cmd/posh/tpl/txn_result.tpl"  )

def nextorder():
    return int(random.randint(1, 999999999999999 ))

creditc = "4012001038443335"
expdat = "1305"
cvcode = "471"


class TestCoposWebCheckout( TestCase ):
    fixtures = ['sites.json', 'l10n.json', 'pages.json', 'tieredweight.json', 'shop.json', 'product.json', 'products.json']

    def setUp(self):
        # Every test needs a client
        self.client = Client()

    def tearDown(self):
        keyedcache.cache_delete()

    def test_checkout_internalerror(self):
        """
        Mantis #12489: Interal server error on /public/shop/checkout/credit/
        """
        # Add product to cart
        cartadd = urlresolvers.reverse( 'satchmo_cart_add' )
        carturl = urlresolvers.reverse( 'satchmo_cart' )
        response = self.client.post( cartadd, { "productname" : "book_postcardsfromuniverse", "addcart" : "Add to cart", "quantity" : '1' }, follow=True )
        self.assertRedirects( response, carturl, status_code = 302, target_status_code = 200 )

        checkout1 = urlresolvers.reverse( 'satchmo_checkout-step1' )
        checkout2 = urlresolvers.reverse( 'COPOSWEB_satchmo_checkout-step2' )
        response = self.client.get( checkout2, follow=True )
        self.assertRedirects( response, checkout1 )

    def test_checkout(self):
        """
        Validate we can add some items to the cart
        """
        # Load product URL
        producturl = urlresolvers.reverse( "satchmo_product", kwargs = { 'product_slug' : 'book_postcardsfromuniverse' } )
        response = self.client.get( producturl )
        self.assertContains( response, "Postcards from the Edge of the Universe", status_code = 200 )

        # Add product to cart
        cartadd = urlresolvers.reverse( 'satchmo_cart_add' )
        carturl = urlresolvers.reverse( 'satchmo_cart' )
        response = self.client.post( cartadd, { "productname" : "book_postcardsfromuniverse", "addcart" : "Add to cart", "quantity" : '1' }, follow=True )
        self.assertRedirects( response, carturl, status_code = 302, target_status_code = 200 )

        # Cart page
        response = self.client.get(carturl)
        self.assertContains( response, "Postcards from the Edge of the Universe", status_code = 200 )

        # Checkout page
        checkout1 = urlresolvers.reverse( 'satchmo_checkout-step1' )
        checkout2 = urlresolvers.reverse( 'COPOSWEB_satchmo_checkout-step2' )
        checkout3 = urlresolvers.reverse( 'COPOSWEB_satchmo_checkout-step3' )
        response = self.client.get( checkout1 )
        self.assertContains( response, "Billing Information", count = 1, status_code = 200 )

        # Post billing information
        response = self.client.post( checkout1, { "paymentmethod" : "PAYMENT_COPOSWEB",
                                                "email" : "lnielsen@spacetelescope.org",
                                                "first_name" : "Lars Holm",
                                                "last_name" : "Nielsen",
                                                "phone" : "+4915122652416",
                                                "addressee" : "",
                                                "street1" : "Karl-Schwarzschild-Str 2",
                                                "street2" : "",
                                                "city" : "Garching bei München",
                                                "state" : "",
                                                "postal_code" : "85748",
                                                "country" : "81",
                                                "copy_address" : "1",
                                                "ship_addressee" : "",
                                                "ship_street1" : "Karl-Schwarzschild-Str 2",
                                                "ship_street2" : "",
                                                "ship_city" : "Garching bei München",
                                                "ship_state" : "",
                                                "ship_postal_code" : "85748",
                                                "ship_country" : "81",
                                                "discount" : "",
                                                "terms" : "yes", # Accept terms
                                                "newsletter" : "yes", # Receive newsletter
                                                }, follow=True )

        self.assertRedirects( response, checkout2, status_code = 302, target_status_code = 200 )

        # Checkout step 2
        response = self.client.get( checkout2 )
        self.assertContains( response, "Payment Information", count = 1, status_code = 200 )
        self.assertContains( response, "Shipping Method", count = 1, status_code = 200 )

        # Post credit card information
        response = self.client.post( checkout2, {   "credit_number" : creditc,
                                                    "month_expires" : "5",
                                                    "year_expires" : "2013",
                                                    "ccv" : cvcode,
                                                    "credit_type" : "Visa",
                                                    "shipping" : "tieredweight_1",
                                                } )

        self.assertRedirects( response, checkout3, status_code = 302, target_status_code = 200 )


        # Checkout step 3
        response = self.client.get( checkout3 )
        self.assertContains( response, "Place order", status_code = 200 )

        # Place order
        successurl = urlresolvers.reverse( 'COPOSWEB_satchmo_checkout-success' )
        response = self.client.post( checkout3, { "Process" : "True" }, follow=True )
        self.assertRedirects( response, successurl, status_code = 302, target_status_code = 200 )

        response = self.client.get( successurl )
        self.assertContains( response, "Order successfully completed", status_code = 200 )


#class TestOrder( TestCase ):
#       self.assertContains(response, "Django Rocks shirt (Large/Blue)", count=1, status_code=200)
#       response = self.client.get(url('satchmo_checkout-step1'))
#       self.assertContains(response, "Billing Information", count=1, status_code=200)
#
#       # now check for min order not met
#       min_order.update("100.00")
#       response = self.client.get(url('satchmo_checkout-step1'))
#       self.assertContains(response, "This store requires a minimum order", count=1, status_code=200)
#
#       # add a bunch of shirts, to make the min order
#       response = self.client.post(cartadd, { "productname" : "dj-rocks",
#                                                     "1" : "L",
#                                                     "2" : "BL",
#                                                     "quantity" : '10'})
#       self.assertRedirects(response, carturl,
#           status_code=302, target_status_code=200)
#       response = self.client.get(url('satchmo_checkout-step1'))
#       self.assertContains(response, "Billing Information", count=1, status_code=200)


manager_api = """
#
# Authorize
>>> transaction = manager.authorization( "hbt000001" , "4012001038443335", "1305", "471", "1230" )
>>> transaction.params["orderid"] == "hbt000001"
True
>>> transaction.params["creditc"] == "4012001038443335"
True
>>> transaction.params["expdat"] == "1305"
True
>>> transaction.params["cvcode"] == "471"
True
>>> transaction.params["amount"] == "1230"
True
>>> transaction.params["command"] == "authorization"
True

#
# Preauthorize
>>> transaction2 = manager.preauthorization( "hbt000001", "4012001038443331", "1301", "472", "1233" )
>>> transaction2.params["orderid"] == "hbt000001"
True
>>> transaction2.params["creditc"] == "4012001038443331"
True
>>> transaction2.params["expdat"] == "1301"
True
>>> transaction2.params["cvcode"] == "472"
True
>>> transaction2.params["amount"] == "1233"
True
>>> transaction2.params["command"] == "preauthorization"
True

#
# Capture
>>> transaction3 = manager.capture( "0510134536061301_01", "1233" )
>>> transaction3.params["trefnum"] == "0510134536061301_01"
True
>>> transaction3.params["amount"] == "1233"
True
>>> transaction3.params["command"] == "capture"
True

#
# Return
>>> transaction4 = manager.return_transaction( "0510134536061301_02", "1232" )
>>> transaction4.params["trefnum"] == "0510134536061301_02"
True
>>> transaction4.params["amount"] == "1232"
True
>>> transaction4.params["command"] == "return"
True

#
# Reversal
>>> transaction5 = manager.reversal( "0510134536061301_03" )
>>> transaction5.params["trefnum"] == "0510134536061301_03"
True
>>> transaction5.params["command"] == "reversal"
True

#
# Transaction result
>>> transaction6 = manager.transaction_result( "0510134536061301_07" )
>>> transaction6.params["trefnum"] == "0510134536061301_07"
True
>>> transaction6.params["command"] == "txnresult"
True
>>> transaction6 = manager.transaction_result( trefnum="0510134536061301_08" )
>>> transaction6.params["trefnum"] == "0510134536061301_08"
True
>>> transaction6.params["command"] == "txnresult"
True
>>> transaction6 = manager.transaction_result( orderid="0510134536061301_09" )
>>> transaction6.params["orderid"] == "0510134536061301_09"
True
>>> transaction6.params["command"] == "txnresult"
True
"""

transaction_api = """
#
# Wrong expire date
>>> transaction = manager.authorization( "hbt%.15d" % nextorder(), creditc, "12345", cvcode, "1230" )
>>> transaction.run()
Traceback (most recent call last):
    ...
CoposWebTransactionError: Expire date is wrong

#
# Wrong card number
>>> transaction = manager.authorization( "hb%.6d" % nextorder(), "1234", expdat, cvcode, "1230" )
>>> transaction.run()
Traceback (most recent call last):
    ...
CoposWebTransactionError: Card number is wrong


#
# Expired card
>>> transaction = manager.authorization( "hb%.6d" % nextorder(), creditc, "0910", cvcode, "1230" )
>>> transaction.run()
Traceback (most recent call last):
    ...
CoposWebTransactionError: Card expired


#
# Good transaction
>>> transaction = manager.authorization( "hb%.6d" % nextorder(), creditc, expdat, cvcode, "2000" )
>>> transaction.run()
>>> transaction.response.posherr == "0"
True

>>> transaction = manager.preauthorization( "hb%.6d" % nextorder(), creditc, expdat, cvcode, "3000" )
>>> transaction.run()
>>> captrans = manager.capture( transaction.response.trefnum, "2000")
>>> captrans.run()

>>> transaction = manager.preauthorization( "hb%.6d" % nextorder(), creditc, expdat, cvcode, "3000" )
>>> transaction.run()
>>> captrans = manager.reversal( transaction.response.trefnum )
>>> captrans.run()

>>> transaction = manager.preauthorization( "hb%.6d" % nextorder(), creditc, expdat, cvcode, "3000" )
>>> transaction.run()
>>> captrans = manager.capture( transaction.response.trefnum, "3000")
>>> captrans.run()
>>> rettrans = manager.return_transaction( captrans.response.trefnum, "1000" )
>>> rettrans.run()
"""

__test__ = {
             'manager' : manager_api,
             'transaction' : transaction_api,
           }

if __name__ == "__main__":
    import doctest
    doctest.testmod()
