"""
Pickup shipping module
"""

# Note, make sure you use decimal math everywhere!
from decimal import Decimal
from shipping.modules.base import BaseShipper
from djangoplicity.archives.contrib.satchmo.esoshipping.utils import validate_contact


class PickupShipper( BaseShipper ):
    flatRateFee = Decimal( "0.00" )
    id = "PUP"
    pickup = True

    def __init__(self, id="", name="", desc="", method="", delivery="", cost="0.00" ):
        self.flatRateFee = Decimal( cost )
        self._name = name
        self._desc = desc
        self._method = method
        self._delivery = delivery
        self.id = id

    def __str__( self ):
        return "HQ Pickup Shipping Rate"

    def description( self ):
        """ A basic description that will be displayed to the user when selecting their shipping options """
        return self._desc

    def cost( self ):
        return self.flatRateFee

    def method( self ):
        """ Describes the actual delivery service (Mail, FedEx, DHL, UPS, etc) """
        return self._method

    def expectedDelivery( self ):
        """
        Can be a plain string or complex calcuation returning an actual date
        """
        return self._delivery

    def valid( self, order=None ):
        return not validate_contact( self.contact )
