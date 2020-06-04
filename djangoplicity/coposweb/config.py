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
Configuration module for custom payment module.

See http://www.satchmoproject.com/docs/rel/0.9.1/custom-payment.html#configuration
"""

from livesettings.functions import config_register_list
from livesettings.values import *

from django.utils.translation import ugettext_lazy as _

# this is so that the translation utility will pick up the string
gettext = lambda s: s

PAYMENT_GROUP = ConfigurationGroup( 'PAYMENT_COPOSWEB',
    _( 'COPOSweb Payment Module Settings' ),
    ordering=100 )

config_register_list(

    BooleanValue( PAYMENT_GROUP,
        'SSL',
        description=_( "Use SSL for the module checkout pages?" ),
        default=True ),

    BooleanValue( PAYMENT_GROUP,
        'LIVE',
        description=_( "Accept real payments" ),
        help_text=_( "False if you want to be in test mode" ),
        default=True ),

    ModuleValue( PAYMENT_GROUP,
        'MODULE',
        description=_( 'Implementation module' ),
        hidden=True,
        default='djangoplicity.coposweb' ),

    StringValue( PAYMENT_GROUP,
        'KEY',
        description=_( "Module key" ),
        hidden=True,
        default='COPOSWEB' ),

    StringValue( PAYMENT_GROUP,
        'LABEL',
        description=_( 'English name for this group on the checkout screens' ),
        default='Credit Cards',
        help_text=_( 'This will be passed to the translation utility' ) ),

    StringValue( PAYMENT_GROUP,
        'URL_BASE',
        description=_( 'The url base used for constructing urlpatterns which will use this module' ),
        default='^credit/' ),

    MultipleStringValue( PAYMENT_GROUP,
        'CREDITCHOICES',
        description=_( 'Available credit cards' ),
        choices=(
            ( ( 'Visa', 'Visa' ) ),
            ( ( 'Mastercard', 'Mastercard' ) ),
            ( ( 'American Express', 'American Express' ) ) ),
        default=( 'Visa', 'Mastercard', 'American Express' ) ),

    BooleanValue( PAYMENT_GROUP,
        'CAPTURE',
        description=_( 'Capture Payment immediately?' ),
        default=False,
        help_text=_( 'IMPORTANT: If false, a capture attempt will be made when the order is marked as shipped."' ) ),

    BooleanValue( PAYMENT_GROUP,
        'EXTRA_LOGGING',
        description=_( "Verbose logs" ),
        help_text=_( "Add extensive logs during post." ),
        default=False ),

    StringValue( PAYMENT_GROUP,
        'LIVE_CONFIG_FILE',
        description=_( "Path to live configuration file." ),
        help_text=_( """Full path to the coposweb.ini configuration file containing web service URL, credentials and more.""" ),
        default='/etc/coposweb.ini' ),

    StringValue( PAYMENT_GROUP,
        'CONNECTION_TEST',
        description=_( "Submit to Test URL" ),
        help_text=_( """This is the address to submit test transactions.""" ),
        default='https://coposweb.companydirect.de/posh/cmd/posh/tpl/txn_result.tpl' ),

    StringValue( PAYMENT_GROUP,
        'USER_TEST',
        description=_( 'Your COPOSweb service test username' ),
        default="" ),

    StringValue( PAYMENT_GROUP,
        'PASSWORD_TEST',
        description=_( 'Your COPOSweb service test password' ),
        default="" ),

    StringValue( PAYMENT_GROUP,
        'AUTH_REALM_TEST',
        description=_( 'Your COPOSweb service test HTTP authentication realm' ),
        default="POSH" ),

    StringValue( PAYMENT_GROUP,
        'AUTH_URL_TEST',
        description=_( 'Your COPOSweb service test HTTP authentication URL' ),
        default="coposweb.companydirect.de" ),

    StringValue( PAYMENT_GROUP,
        'CURRENCY_TEST',
        description=_( 'Your COPOSweb service test currency.' ),
        default="EUR" ),
)
