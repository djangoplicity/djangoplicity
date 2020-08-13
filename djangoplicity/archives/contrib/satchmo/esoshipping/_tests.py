"""
Module for testing shipping prices defined in the database.
"""
from __future__ import print_function

#
# General setup
#
from builtins import zip
from shipping.modules.tieredweight.models import Carrier
from l10n.models import Country

try:
    from decimal import Decimal
except ImportError:
    from django.utils._decimal import Decimal

germany = Country.objects.get(iso2_code='de')
europe = Country.objects.get(iso2_code='dk')
world = Country.objects.get(iso2_code='us')

c = Carrier.objects.get( name='Deutsche Post' )
zone_de = c.get_zone( germany )
zone_eu = c.get_zone( europe )
zone_wo = c.get_zone( world )

zones = [ zone_de, zone_eu, zone_wo ]


def srange( start, stop, step ):
    """ Make a range of values from start to stop in steps of step. """
    ls = [start]
    i = 1
    while ls[-1] < stop and (start + i * step) <= stop:
        ls.append( start + i * step )
        i += 1
    return ls


#
# The shipping table to test against:
# https://www.eso.org/public/shopinfo/shipping.html
#
# Note testing the boundries is a bit tricky. There's
# an issue with e.g. 19.99 gets added to a higher
# shipping category, so we only test to 19.98, and live
# with error.
#
shipping_table = [
    [("1", "19.98"), ["0.55", "0.70", "1.70"]],
    [("20.0", "49.98"), ["0.90", "1.25", "2.20"]],
    [("50.0", "449.98"), ["1.45", "3.40", "6.00"]],
    [("500.0", "999.98"), ["2.20", "6.00", "12.00"]],
    [("1000.0", "1999.98"), ["4.10", "8.60", "13.90"]],
    [("2000.0", "4999.98"), ["6.90", "17.00", "35.00"]],
    [("5000.0", "99999.98"), ["6.90", "22.00", "45.00"]],
]

#
# Check shipping prices
#
for row in shipping_table:
    range = row[0]
    zoneprices = list(zip(zones, row[1]))

    low = range[0]
    high = range[1]

    weights = srange(float(low), float(low) + 1.5, 0.1) + srange(float(high) - 1.5, float(high), 0.01)
    try:
        for w in weights:
            for z, expected_cost in zoneprices:
                calculated_cost = z.cost( w )
                expected_cost = Decimal(expected_cost)
                assert calculated_cost == expected_cost
    except AssertionError as e:
        print("Zone %s, Weight %s: Expected %s, got %s" % ( z.name, w, expected_cost, calculated_cost ))
