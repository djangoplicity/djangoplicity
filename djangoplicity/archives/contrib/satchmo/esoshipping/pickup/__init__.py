def get_methods():
    from django.conf import settings
    from djangoplicity.archives.contrib.satchmo.esoshipping.pickup.shipper import PickupShipper

    if hasattr( settings, "SHOP_PICKUP_LOCATIONS" ):
        return [PickupShipper(**locdict) for locdict in settings.SHOP_PICKUP_LOCATIONS]
    else:
        return []
