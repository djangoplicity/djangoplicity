from django.conf.urls import url

from satchmo_store.shop.satchmo_settings import get_satchmo_setting
from payment.views.confirm import confirm_free_order

from djangoplicity.concardis.views import pay_ship_info, confirm_info, \
    feedback, success

ssl = get_satchmo_setting('SSL', default_value=False)

urlpatterns = [
    url(r'^$', pay_ship_info, {'SSL': ssl}, 'CONCARDIS_satchmo_checkout-step2'),
    url(r'^confirm/$', confirm_info, {'SSL': ssl}, 'CONCARDIS_satchmo_checkout-step3'),
    url(r'^success/$', success, {'SSL': ssl}, 'CONCARDIS_satchmo_checkout-success'),
    url(r'^feedback/$', feedback, name='CONCARDIS_satchmo_checkout-feedback'),
    url(r'^confirmorder/$', confirm_free_order,
        {'SSL': ssl, 'key': 'CONCARDIS'}, 'CONCARDIS_satchmo_checkout_free-confirm')
]
