from djangoplicity.archives.contrib.satchmo.esoshipping.pickup.shipper import PickupShipper


def get_methods():
    from django.conf import settings

    if hasattr( settings, "SHOP_PICKUP_LOCATIONS" ):
        return [PickupShipper(**locdict) for locdict in settings.SHOP_PICKUP_LOCATIONS]
    else:
        return []
