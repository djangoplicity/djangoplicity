"""
Pickup shipping module
"""

# Note, make sure you use decimal math everywhere!
from decimal import Decimal
from django.utils.translation import ugettext_lazy as _
from shipping.modules.base import BaseShipper
from django.conf import settings
from djangoplicity.archives.contrib.satchmo.esoshipping.utils import validate_contact

if hasattr( settings, "EMPLOYEE_DISCOUNT_PREFIX" ):
    EMPLOYEE_DISCOUNT_PREFIX = settings.EMPLOYEE_DISCOUNT_PREFIX
else:
    EMPLOYEE_DISCOUNT_PREFIX = "EMPLOYEE"


class Shipper( BaseShipper ):
    flatRateFee = Decimal( "0.00" )
    id = "ESOO"

    def __str__( self ):
        return "ESO Employee Shipping Rate"

    def description( self ):
        """ A basic description that will be displayed to the user when selecting their shipping options """
        return _( "Office delivery for ESO employees" )

    def cost( self ):
        return self.flatRateFee

    def method( self ):
        """ Describes the actual delivery service (Mail, FedEx, DHL, UPS, etc) """
        return "Sent via ESO internal mail."

    def expectedDelivery( self ):
        """
        Can be a plain string or complex calcuation returning an actual date
        """
        return "Only available in Garching & Vitacura! For standard postal delivery please go back to the previous page and enter a non @eso.org email address."

    def valid( self, order=None ):
        """
        Make office delivery available for orders that come from an @eso.org address.
        """
        return validate_contact( self.contact )
