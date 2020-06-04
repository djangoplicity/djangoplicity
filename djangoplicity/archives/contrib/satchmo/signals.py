import django.dispatch

warehouse_for_orderitems = django.dispatch.Signal( providing_args=["orderitems", ] )
