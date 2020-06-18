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
Module for interacting with the COPOSweb service for credit card
payments.

Example::
    manager = CoposWebManager( user="...", password="..." )
    transaction = transaction = manager.authorization( "orderid" , "1234123412341234", "1305", "471", "1230" )
    try:
        transaction.run()
    except CoposWebTransactionError, e:
        ... # Payment error (remote)
    except CoposWebError, e:
        ... # Local error
        
        
COPOSweb card transactions
==========================

Authorization
-------------
Summary: Credit card holder is charged immediately.

This sends an authorization and capture request (also known as: auth/capture, authorization, purchase). 
An "authorization" is a request to charge a cardholder, which can be declined or approved by the card issuer. In 
case of an approval, the issuer assigns an authorization identifier and charges the card limit with the 
requested amount. Charging the card account and crediting the merchant account are separate processes.

In the model "authorization and capture", the capture will be executed automatically by closing the cash 
accounts at end-of-day without another action from the merchant. This model implies that the business 
transaction has been completed at the time of the purchase, e.g. the goods have been delivered or the 
service access granted.

Preauhtorization
----------------
Summary: Credit card holder is *not* charged until you send another *capture* request.

In the model "preauthorization", a subsequent capture transaction follows the authorization message. This 
model will be suitable if the merchant fulfills the order some time later, but wants an authorization for 
the customer's card at the time the order is placed.

Capture
-------
Any preauhtorization transaction must be followed later by a capture transaction to debit the credit card
holder. Otherwise no money is transferred to the merchant account. Please note that a preauthorization 
is only valid for a limited period.

Reversal
--------
In both models, authorizations can be reversed. A reversed (canceled) authorization is not debited to the customer's 
card account. In the model "authorization" a reversal is possible until closing the cash accounts at 
end-of-day, in the model "preauthorization" it is possible until a subsequent capture transaction is 
transmitted or until the issuer's reservation period has expired.

Refunds
-------
Refunds are transactions that are authorized and captured directly. In these cases the authorization makes sure that 
the presented card really exists.
"""

import cgi
import re
import socket
import urllib
import urllib2

def alpha( len, allow_none=True  ):
    """
    Function factory for creating a validator function 
    for alphanumeric strings.
    """
    len = int(len)
    
    if int(len) < 0:
        raise Exception( "Length must be greater than zero." )
    
    def f( value ):
        if not allow_none and value is None:
            raise AttributeError
        elif value is None:
            value = [""]
        
        return str( value[0] )[:len]
    
    return f


class CoposWebError( Exception ):
    """
    Exception for errors that happen in our end. Typical errors
    can be that a connection cannot be established to the 
    payment processor's servers.
    """
    
    def __init__(self, msg, exception=None ):
        self.triggered_exception = exception
        super( CoposWebError, self ).__init__( msg )
    

class CoposWebTransactionError( CoposWebError ):
    """
    Exception for errors in the COPOSweb service - i.e. errors
    that happen in the payment processor's end. Typical this is 
    because the the payment processor cannot validate because e.g. 
    the expire date, CVC, card number is wrong or the card is closed 
    
    The exception contains two error messages:
      * User error message 
      * System error message.
      
    The user message can be displayed to an end-user while, a system
    error message contains more specific information but should not be
    displayed to end users.
    
    The system message can be accessed via::
        e.system_message
    """
    
    rc_msgs = {
        "005" : "Authorization declined - expire date or card verification value might be incorrect.",
        "033" : "Card expired",
        "090" : "Card issuer temporarily not reachable",
        "091" : "Card issuer temporarily not reachable",
    }
    
    posherr_msg = {
        "0" : "Approved transaction",
        "100" : "Transaction declined by card issuer", # changed
        "2014" : "Card number is wrong", # changed
        "2016" : "Expire date is wrong", # changed
        "2018" : "Card validation value is wrong",
        "2040" : "Prefix or length of card number incorrect",
        "2042" : "Check digit of card number incorrect",
        "2048" : "Card expired",
    }
    
    def _make_msg(self):
        """
        Generate an error message that can be displayed to the end user.
        """
        if self.posherr == "100":
            if self.rc in self.rc_msgs:
                return self.rc_msgs[self.rc]
            else:
                return self.posherr_msg[self.posherr]
        elif self.posherr in self.posherr_msg:
            return self.posherr_msg[self.posherr]
        
        return "Payment currently not possible due to problems at the bank or card issuer. You might try to checkout again in a few minutes - if there still problems then please contact us."
    
    def __init__(self, response ):
        self.posherr = response.posherr
        if self.posherr == "100": 
            self.rc = response.rc
        else:
            self.rc = None
            
        self.system_message = response.rmsg
        super( CoposWebTransactionError, self ).__init__( self._make_msg() )



class CoposWebResponse( object ):
    """
    COPOSweb response class.
    
    Encapsulates a response from the COPOSweb service, and allow access
    to the individual fields of the response as attributes. 
    
    Example::
        transaction.response.posherr
        transaction.response.trefnum
        
    Note depending on the command executed not all fields in the response 
    may be available, and thus an AttributeError might be raised if this 
    is the case.
    """
    _attributes = {
        'aid' : alpha(8),
        'amount' : alpha(12),
        'cai'  : alpha(19),
        'creditc' : alpha(19),
        'currency' : alpha(3),
        'expdat' : alpha(4),
        'merch_name' : alpha(50),
        'merch_tid' : alpha(8),
        'orderid' : alpha(27),
        'posherr' : alpha(5), # Result from COPOSweb service
        'rc' : alpha(3, allow_none=True ), # Response code acquiring processor
        'retrefnr' : alpha(6), # Trace number
        'rmsg' : alpha(80, allow_none=True ),
        'timestamp' : alpha(14), # UTC
        'trefnum' : alpha(30, allow_none=True ), # Transaction identifier
        'txn_card' : alpha(40),
        'txntype' : alpha(50),
    } 
    
    def __init__( self, response ):
        """
        Parses the application/x-www-form-urlencoded response from the 
        COPOSweb service. 
        """
        self._response = cgi.parse_qs( response )
        
    def __getattr__( self, name ):
        """
        Allow attribute access to fields of response.
        
        Also applies an checking function that ensures that the 
        response is properly formatted and of a proper datatype.
        """
        if name in self._attributes:
            try:
                val = self._response[name]
            except KeyError:
                val = None
            
            return self._attributes[name]( val )
        raise AttributeError

    
class CoposWebTransaction(object):
    """
    COPOSweb transaction class
    
    WARNING:: This class is instantiated by the CoposWebManager and should not be instantiated 
    directly by the user!
    
    It is responsible for sending a POST request to the COPOSweb service, 
    retrieving the response and 
    """
    
    def __init__( self, conf, params, timeout = 35 ):
        self.conf = conf
        self.params = params
        self.timeout = timeout
        self.response = None
    
    def _url_opener( self ):
        """
        Create URL opener for sending a request to the COPOSweb service.
        """
        # Create authentication handler and URL opener
        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password( self.conf['auth_realm'], self.conf['auth_url'], self.conf['user'], self.conf['password'] )       
        opener = urllib2.build_opener( auth_handler )
        
        return opener
    
    def _post_data( self ):
        """
        URL encode the parameters.
        """
        # Encode POST data
        return urllib.urlencode( self.params )
    
    def _post_request( self ):
        """
        Send the POST request and retrieve the data.
        """
        # Set socket timeout
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout( self.timeout )
        
        # Send POST request, read response and close connection
        try:
            opener = self._url_opener()
            f = opener.open( self.conf['url'], self._post_data() )
            response = f.read()
            f.close()
        except ( urllib2.URLError, urllib2.HTTPError ) as e:
            raise CoposWebError( "A communication problem with our credit card payment provider has occurred. Please come back later. Your card has not been charged.", exception=e )
        finally:
            socket.setdefaulttimeout( old_timeout )

        # Set back old timeout
        return response
        

    def run( self ):
        """
        Run the transaction.
        
        This method will throw either a CoposWebError or CoposWebTransactionError in
        case of problems during the transaction. In case no exceptions are raised, the
        transaction completed successfully.
        """
        data = self._post_request()
        
        try:
            self.response = CoposWebResponse( data )
            
            posherr = self.response.posherr
            if posherr != "0":
                raise CoposWebTransactionError( self.response )
        except AttributeError as e:
            raise CoposWebError( "A communication problem with our credit card payment provider has occurred. Please come back later. Your card has not been charged.", exception=e )



class TestTransaction( CoposWebTransaction ):
    """
    Transaction class used for testing web payments without actually interacting with coposweb.
    It takes the same parameters as CoposWebTransaction
    
    WARNING:: This class is instantiated by the CoposWebManager and should not be instantiated 
    directly by the user!
    """
    def _url_opener( self ):
        """
        Create URL opener for sending a request to the COPOSweb service.
        """
        # Create authentication handler and URL opener
        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password( self.conf['auth_realm'], self.conf['auth_url'], self.conf['user'], self.conf['password'] )       
        opener = urllib2.build_opener( auth_handler )
        
        return opener
    
    def _post_request( self ):
        """
        Fake the POST request
        """
        if self.conf['auth_realm'] != "POSH" \
            or self.conf['auth_url'] != "coposweb.companydirect.de" \
            or self.conf['user'] != "test" \
            or self.conf['password'] != "test":
            pass # return emulate 404
            
        
        
#       urllib.urlencode( self.params )
#       
#       try:
#           opener = self._url_opener()
#           f = opener.open( self.conf['url'], self._post_data() )
#           response = f.read()
#           f.close()
#       except ( urllib2.URLError, urllib2.HTTPError ), e:
#           raise CoposWebError( "A communication problem with our credit card payment provider has occurred. Please come back later. Your card has not been charged.", exception=e )
#       finally:
#           socket.setdefaulttimeout( old_timeout )
#
#       # Set back old timeout
#       return response





class CoposWebManager( object ):
    def __init__( self, user=None, password=None, url="https://coposweb.companydirect.de/posh/cmd/posh/tpl/txn_result.tpl", auth_realm="POSH", auth_url="coposweb.companydirect.de", currency='EUR', transactioncls=CoposWebTransaction ):
        self.conf = {}
        self.conf['user'] = user
        self.conf['password'] = password
        self.conf['url'] = url
        self.conf['auth_realm']=auth_realm
        self.conf['auth_url']=auth_url
        self.conf['currency']=currency
        self._transactioncls = transactioncls

    def _create_auth_transaction( self, orderid, creditc, expdat, cvcode, amount, cmd ):
        """
        Internal method.
        
        Setup parameters for an authorization or preauthorization transaction.
        """
        params = {
            'command' : str(cmd)[:16], #16a
            'orderid' : str(orderid)[:27], #27a
            'creditc' : str(creditc)[:19], #19n
            'expdat' : str(expdat)[:4], #4n
            'cvcode' : str(cvcode)[:4], #4n
            'currency' : str(self.conf['currency'])[:3], #3a
            'amount' : str(amount)[:12], #12n
        }
        
        return self._transactioncls( self.conf, params )
        
    def authorization( self, orderid, creditc, expdat, cvcode, amount ):
        """
        Create an authorization transaction
        
        AMOUNT IN CENTS !!!
        """
        return self._create_auth_transaction( orderid, creditc, expdat, cvcode, amount, "authorization" )
        
    def preauthorization( self, orderid, creditc, expdat, cvcode, amount ):
        """
        Create an preauthorization transaction.
        
        AMOUNT IN CENTS !!! 
        """
        return self._create_auth_transaction( orderid, creditc, expdat, cvcode, amount, "preauthorization" )
    
    def refund( self, orderid, creditc, expdat, cvcode, amount ):
        """
        Create refund transaction
        
        AMOUNT IN CENTS !!! 
        """
        raise NotImplementedError
        #return self._create_auth_transaction( orderid, creditc, expdat, cvcode, amount, "refund" )
        
    def capture( self, trefnum, amount ):
        """
        cmd, Transaction type: return
        trefnum, Transaction number of the preauthorization transaction
        amount, Amount in minor currency unit
        
        Note only one capture per preauthorization is allowed
        
        AMOUNT IN CENTS !!!
        """
        params = {
            'command' : 'capture', #16a
            'trefnum' : trefnum, #30a
            'amount' : amount, #12n
        }
        return self._transactioncls( self.conf, params )
        
    def return_transaction( self, trefnum, amount ):
        """
        cmd, Transaction type: return
        trefnum, Transaction number of the authorization or capture transaction
        amount, Amount in minor currency unit
        
        AMOUNT IN CENTS !!!
        """
        params = {
            'command' : 'return', #16a
            'trefnum' : trefnum, #30a
            'amount' : amount, #12n
        }
        return self._transactioncls( self.conf, params )
        
    def reversal( self, trefnum ):
        """
        cmd, Transaction type: return
        trefnum, Transaction number of the transaction to be cancelled
        amount, Amount in minor currency unit
        
        AMOUNT IN CENTS !!!
        """
        params = {
            'command' : 'reversal', #16a
            'trefnum' : trefnum, #30a
        }
        return self._transactioncls( self.conf, params )
        
    def transaction_result( self, trefnum=None, orderid=None ):
        """
        Transaction type: txnresult (Request the result of a finished transaction again, if the reply has been lost)
        
        Only supply either trefnum or orderid - not both.
        
        trefnum, Transaction number of the requested transaction
        Order id; command will return the last result of the transactions with this id
        """
        if trefnum:
            params = {
                'command' : 'txnresult', #16a
                'trefnum' : trefnum, #30a
            }
        elif orderid:
            params = {
                'command' : 'txnresult', #16a
                'orderid' : orderid, #27a
            }
        else:
            raise Exception
        return self._transactioncls( self.conf, params )
