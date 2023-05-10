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
Satchmo payment processor - http://www.satchmoproject.com/docs/rel/0.9.1/custom-payment.html#building-your-processor

Basically it's an bridge between Satchmo and the manager.CoposWebManager.
"""
from __future__ import print_function
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
from builtins import str
from django.utils.translation import ugettext_lazy as _
from payment.modules.base import BasePaymentProcessor, ProcessorResult
from .manager import CoposWebManager, CoposWebError, CoposWebTransactionError
from django.conf import settings as djsettings
from decimal import Decimal
import os

def format_expdat( expdat ):
    month,year = expdat.split("/")
    return "%s%.2d" % ( year[2:4], int( month ) )

def format_amount( amount ):
    return int( amount * 100 )

def get_order_id():
    filepath = os.path.join( djsettings.TMP_DIR, "orderid.txt" )
    
    if os.path.exists( filepath ):
        f = open( filepath )
        no = int( f.read() )
        f.close()
        
        if( no < 999999 ):
            no += 1
            f = open( filepath, 'w' )
            f.write( str(no) )
            f.close()
            
            return no
    else:
        f = open( filepath, 'w' )
        f.write( "1" )
        f.close()
        return 1

class PaymentProcessor( BasePaymentProcessor ):
    def __init__( self, settings ):
        super( PaymentProcessor, self ).__init__( 'coposweb', settings )
        # Initialize a copos web manager with the correct settings
        self.manager = self.coposweb_manager( settings )
        
    def next_order_id( self ):
        """
        Generate an order id
        """
        return "%s%.6d" % ( djsettings.ORDER_PREFIX, get_order_id() )
        
    def prepare_data(self, order):
        super( PaymentProcessor, self ).prepare_data( order )
        
        # Generate new order id.
        try:
            self.erp_order_id = order.get_variable( "ORDER_ID" ).value
        except AttributeError:
            self.erp_order_id = self.next_order_id()
            order.add_variable( "ORDER_ID", self.erp_order_id )

    def coposweb_manager( self, settings ):
        """
        Create CoposWebManager with proper URL, username and password for e.g. live/test environments.
        """
        if self.is_live():
            self.log_extra('Using live connection.')
            
            ini_file = settings.LIVE_CONFIG_FILE.value
            if not os.path.exists( ini_file ):
                self.log.error('COPOSweb config file %s does not exists.' % ini_file )
                raise Exception("COPOSweb payment module configuration problem - credentials file does not exists.")
                
            from configparser import ConfigParser
            config = ConfigParser()
            config.read( ini_file )
            
            url = config.get("COPOSweb","URL")
            user = config.get("COPOSweb","USER")
            password = config.get("COPOSweb","PASSWORD")
            auth_realm  = config.get("COPOSweb","AUTH_REALM")
            auth_url = config.get("COPOSweb","AUTH_URL")
            currency = config.get("COPOSweb","CURRENCY")
        else:
            self.log_extra('Using test connection.')
            testflag = 'TRUE'
            url = settings.CONNECTION_TEST.value
            user = settings.USER_TEST.value
            password = settings.PASSWORD_TEST.value
            auth_realm = settings.AUTH_REALM_TEST.value
            auth_url = settings.AUTH_URL_TEST.value
            currency = settings.CURRENCY_TEST.value

        self.log_extra('Using COPOSweb URL %s and currency %s', url, currency )
        return CoposWebManager( user=user, password=password, url=url, auth_realm=auth_realm, auth_url=auth_url, currency=currency )

    
    def coposweb_run_transaction( self, transaction, order, amount, authorization=None ):
        """
        Execute a CoposWebTransaction and return a processor result.
        """
        # Run transaction
        try:
            self.log_extra( "Running COPOSweb %s transaction for order %s", order )
            transaction.run()
            self.log_extra( "COPOSweb preauthorization/authorization/capture transaction for order %s was successful", order )
            
            # Record authorization/preauthorization/capture
            cmd = transaction.params['command']
            
            if cmd == "authorization":
                record = self.record_payment( order=order, amount=amount, transaction_id=transaction.response.trefnum, reason_code = '0' )
                msg = _("Approved and completed successfully")
            elif cmd == "preauthorization":
                record = self.record_authorization( order = order, amount = amount, transaction_id = transaction.response.trefnum, reason_code = '0' )
                msg = _("Approved")
            elif cmd == "capture":
                record = self.record_payment( order=order, amount=amount, transaction_id=transaction.response.trefnum, reason_code = '0', authorization=authorization )
                msg = _("Capture completed successfully") 
            
            return ProcessorResult( self.key, True, msg, record )
        except CoposWebTransactionError as e:
            # Handle remote errors
            self.log.error( "COPOSweb remote error: %s (posherr: %s, rc: %s) " % ( e.system_message, e.posherr, e.rc ) )
            
            payment = self.record_failure( 
                                        order = order, 
                                        amount = amount, 
                                        transaction_id = transaction.response.trefnum, 
                                        reason_code = "%s/%s" % ( e.posherr, e.rc if e.rc else "-" ), 
                                        details = e.system_message,
                                        authorization=authorization,
                                    )
            
            return ProcessorResult( self.key, False, _( str( e ) ) )
        except CoposWebError as e:
            # Handle local errors
            self.log.error( "COPOSweb local error: %s", str( e.triggered_exception ) if e.triggered_exception else "no additional information" )
            
            payment = self.record_failure( 
                                        order = order, 
                                        amount = amount, 
                                        transaction_id = "", 
                                        reason_code = "", 
                                        details = str( e.triggered_exception )[:254],
                                        authorization=authorization,
                                    )
            
            return ProcessorResult( self.key, False, _( str( e ) ) )    

        
    def can_authorize( self ):
        return True

    def authorize_or_capture_payment(self, factory_method, order = None, testing = False, amount = None ):
        try:
            if order:
                self.prepare_data( order )
            else:
                order = self.order
                
            if amount == None:
                amount = order.balance
                
            if order.paid_in_full:
                self.log_extra( '%s is paid in full, no capture attempted.', order )
                self.record_payment()
                return ProcessorResult( self.key, True, _( "No charge needed, paid in full." ) )
            
            self.log.info( 'Authorization/preauthorization for COPOSweb payment for %s' % order )
            
            if not self.is_live():
                self.log.debug( "Creating transaction with %s (id), %s (cc), %s (exp) at %s (amount)" % (order.id, order.credit_card.decryptedCC, format_expdat(order.credit_card.expirationDate), format_amount(amount)) )
            
            # Create transaction
            orderid = order.get_variable("ORDER_ID").value
            self.log_extra("Order id %s" % orderid )
            transaction = factory_method( 
                                            orderid,
                                            order.credit_card.decryptedCC,
                                            format_expdat( order.credit_card.expirationDate ), 
                                            order.credit_card.ccv,
                                            format_amount( amount ) 
                                        )
            
            # Run transaction and return result
            return self.coposweb_run_transaction( transaction, order, amount  )
        except Exception as e:
            import traceback
            self.log.error( "Satchmo error traceback: %s", str( traceback.format_exc( e ) ) )
            print(traceback.format_exc( e ))
            return ProcessorResult( self.key, False, _( "An unexpected error occurred." ) )

    def capture_payment( self, testing = False, amount = None, order=None ):
        """
        Called if can_authorize returns true and config value allows to preauthorize/capture
        """
        self.log_extra( "Capturing payment for order %s" % order )
        return self.authorize_or_capture_payment( self.manager.authorization, testing=testing, order=order, amount=amount )
    
    def authorize_payment( self, order = None, testing = False, amount = None ):
        """
        Make an authorization for an order.  This payment will then be captured when the order
        is set marked 'shipped'.
        """
        self.log_extra("Preauthorizing payment for order %s" % order )
        return self.authorize_or_capture_payment( self.manager.preauthorization, testing=testing, order=order, amount=amount )

    def capture_authorized_payment( self, authorization, testing=False, order=None, amount=None ):
        """
        Given a prior authorization, capture remaining amount not yet captured.
        """
        try:
            if order:
                self.prepare_data(order)
            else:
                order = self.order
            
            if order.authorized_remaining == Decimal('0.00'):
                self.log_extra( 'No remaining authorizations on %s', order )
                return ProcessorResult( self.key, True, _( "Already complete" ) )
    
            if amount == None:
                amount = authorization.remaining()
    
            self.log.info( 'Capture for COPOSweb payment for %s' % order )
            
            if not self.is_live():
                self.log.debug( "Creating capture transaction with %s (id), %s (trefnum) at %s (amount)" % (order.id, authorization.transaction_id, format_amount(amount)) )
            
            # Create transaction
            transaction = self.manager.capture( authorization.transaction_id, format_amount( amount ) )
            
            # Run transaction and return result
            return self.coposweb_run_transaction( transaction, order, amount, authorization=authorization  )
        except Exception as e:
            import traceback
            self.log.error( "Satchmo capture error traceback: %s", str( traceback.format_exc( e ) ) )
            return ProcessorResult( self.key, False, _( "An unexpected error occurred." ) )
