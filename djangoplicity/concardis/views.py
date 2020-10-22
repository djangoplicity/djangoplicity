from __future__ import unicode_literals
from builtins import str
import logging
import os
from collections import OrderedDict

from django.conf import settings
from django.core import urlresolvers
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache

from livesettings.functions import config_get_group, config_value
from payment.config import gateway_live
from payment.utils import get_processor_by_key
from payment.views import payship
from satchmo_store.shop.models import Cart
from satchmo_store.shop.models import Order, OrderPayment
from satchmo_store.contact.models import Contact
from satchmo_utils.dynamic import lookup_url, lookup_template
from satchmo_utils.views import bad_or_missing

from .utils import get_params, get_payment_status, sha1_sign

import django
if django.VERSION >= (2, 2):
    from django.urls import reverse
else:
    from django.core.urlresolvers import reverse

log = logging.getLogger(__name__)

def _get_order_id():
    '''
    Get the next order ID from file
    '''
    filepath = os.path.join(settings.SHARED_DIR, 'orderid.txt')

    no = 1

    if os.path.exists(filepath):
        f = open(filepath)
        no = int(f.read())
        f.close()

        if no < 999999:
            no += 1
            f = open(filepath, 'w')
            f.write(str(no))
            f.close()
    else:
        f = open(filepath, 'w')
        f.write('1')
        f.close()

    return '%s%.6d' % (settings.ORDER_PREFIX, no)


def _verify_feedback(request, order, params):
    '''
    Extract the payment feedback parameters from the request and update
    the order accordingly
    Returns a string in case of error, None otherwise
    '''

    # Calculate the sha1 digest to make sure the parameters haven't been
    # tempered with
    payment_module = config_get_group('PAYMENT_CONCARDIS')
    passphrase = payment_module.SHA_OUT_PASSPHRASE.value
    digest = sha1_sign(params, passphrase)

    if digest and (digest != request.GET.get('SHASIGN')):
        log.info('Invalid SHASIGN for order %s, got "%s", expected: "%s"',
            order, digest, request.GET.get('SHASIGN'))

        return _('Unexpected parameters when processing request, please '
            'contact epodweb@eso.org.')

    pay_id = params['PAYID']
    amount = params['AMOUNT']

    # If the payment hasn't already been processed:
    if not OrderPayment.objects.filter(transaction_id=pay_id).count():
        processor = get_processor_by_key('PAYMENT_CONCARDIS')

        status, status_verbose = get_payment_status(params)

        kwargs = {
            'order': order,
            'amount': amount,
            'transaction_id': pay_id,
            'reason_code': status_verbose,
        }

        if status.startswith('9'):
            order.add_status(status='New', notes=_('Paid through Concardis'))
            processor.record_payment(**kwargs)
        elif status.startswith('5'):
            processor.record_authorization(**kwargs)
        else:
            processor.record_failure(**kwargs)

        # Save the payment parameters
        if order.notes:
            notes = order.notes + '\n'
        else:
            notes = ''

        notes += '--- Concardis payment parameters ---\n'
        for key, val in list(params.items()):
            notes += '{}: {}\n'.format(key, val)

        order.notes = notes
        order.save()

    # Added to track total sold for each product
    for item in order.orderitem_set.all():
        product = item.product
        product.total_sold += item.quantity
        if config_value('PRODUCT', 'TRACK_INVENTORY'):
            product.items_in_stock -= item.quantity
        product.save()

    # Clean up cart now, the rest of the order will be cleaned on paypal IPN
    for cart in Cart.objects.filter(customer=order.contact):
        cart.empty()


@never_cache
def pay_ship_info(request):
    return payship.base_pay_ship_info(request,
        config_get_group('PAYMENT_CONCARDIS'), payship.simple_pay_ship_process_form,
        'shop/checkout/concardis/pay_ship.html')


@never_cache
def confirm_info(request):
    payment_module = config_get_group('PAYMENT_CONCARDIS')

    try:
        order = Order.objects.from_request(request)
    except Order.DoesNotExist:
        url = lookup_url(payment_module, 'satchmo_checkout-step1')
        return HttpResponseRedirect(url)

    tempCart = Cart.objects.from_request(request)
    if tempCart.numItems == 0 and not order.is_partially_paid:
        template = lookup_template(payment_module, 'shop/checkout/empty_cart.html')
        return render(request, template)

    # Check if the order is still valid
    if not order.validate(request):
        return render(request, 'shop/404.html', {
            'message': _('Your order is no longer valid.')
        })

    # Make sure the order has an ORDER_ID
    try:
        order_id = order.get_variable('ORDER_ID').value
    except AttributeError:
        order_id = _get_order_id()
        order.add_variable('ORDER_ID', order_id)

    template = lookup_template(payment_module, 'shop/checkout/concardis/confirm.html')
    if payment_module.LIVE.value:
        log.debug("live order on %s", payment_module.KEY.value)
        url = payment_module.POST_URL.value
    else:
        url = payment_module.POST_TEST_URL.value

    try:
        address = lookup_url(payment_module,
            payment_module.RETURN_ADDRESS.value, include_server=True)
    except urlresolvers.NoReverseMatch:
        address = payment_module.RETURN_ADDRESS.value

    try:
        cart = Cart.objects.from_request(request)
    except:  # pylint: disable=bare-except
        cart = None
    try:
        contact = Contact.objects.from_request(request)
    except:  # pylint: disable=bare-except
        contact = None
    if cart and contact:
        cart.customer = contact
        log.debug(':::Updating Cart %s for %s', cart, contact)
        cart.save()

    processor_module = payment_module.MODULE.load_module('processor')
    processor = processor_module.PaymentProcessor(payment_module)
    processor.create_pending_payment(order=order)
    default_view_tax = config_value('TAX', 'DEFAULT_VIEW_TAX')

    recurring = None

    passphrase = payment_module.SHA_IN_PASSPHRASE.value

    address_b = order.contact.billing_address

    # Add return URLs
    accept_url = 'https://{}{}'.format(
        settings.SITE_DOMAIN,
        reverse('CONCARDIS_satchmo_checkout-success'),
    )

    params = OrderedDict((
        ('ACCEPTURL', accept_url),
        ('AMOUNT', int(order.balance * 100)),  # Amount without decimals
        ('CN', order.contact.first_name + ' ' + order.contact.last_name),
        ('CURRENCY', payment_module.CURRENCY_CODE.value),
        ('EMAIL', order.contact.email),
        ('OPERATION', 'SAL'),  # Set payment to direct sale
        ('ORDERID', order_id),
        ('OWNERADDRESS', ' '.join([address_b.street1, address_b.street2])),
        ('OWNERCTY', address_b.country.iso2_code),
        ('OWNERTOWN', address_b.city),
        ('OWNERZIP', address_b.postal_code),
        ('PARAMVAR', settings.SHORT_NAME),  # Used to identify site in callbacks
        ('PSPID', payment_module.PSPID.value),
    ))

    # Create a sha1 digest of the parameters
    params['SHASIGN'] = sha1_sign(params, passphrase)

    # Make sure params are sorted alphabetically
    params = OrderedDict(sorted(list(params.items()), key=lambda t: t[0]))

    return render(request, template, {'order': order,
        'post_url': url,
        'default_view_tax': default_view_tax,
        'return_address': address,
        'subscription': recurring,
        'PAYMENT_LIVE': gateway_live(payment_module),
        'params': params,
    })


@never_cache
def feedback(request):
    '''
    Captures the server-to-server feedback and update the order accordingly.
    '''
    # Build a dictionary with the URL parameters
    params = get_params(request)

    try:
        order = Order.objects.get(variables__key='ORDER_ID', variables__value=params['ORDERID'])
        # TODO: handle KeyError if no ORDERID is given
    except Order.DoesNotExist:
        # TODO: Log Feedback for non-existing order (email notification?)
        return bad_or_missing(request,
            _('Your order has already been processed.'))

    log.info('Params for order %s', order)
    for key, val in list(params.items()):
        log.info('%s: %s', key, val)

    error = _verify_feedback(request, order, params)

    if error:
        return bad_or_missing(request, error)

    return HttpResponse('OK')


@never_cache
def success(request):
    """
    The order has been succesfully processed.
    We clear out the cart but let the payment processing get called by IPN
    """
    try:
        order = Order.objects.from_request(request)
    except Order.DoesNotExist:
        return bad_or_missing(request,
            _('Your order has already been processed.'))

    # Build a dictionary with the URL parameters
    params = get_params(request)

    log.info('Params for order %s', order)
    for key, val in list(params.items()):
        log.info('%s: %s', key, val)

    # Verify the feedback unless the order has already been paid,
    # e.g in the case of free orders
    if not order.paid_in_full:
        error = _verify_feedback(request, order, params)

        if error:
            return bad_or_missing(request, error)

    del request.session['orderID']
    return render(request, 'shop/checkout/success.html', {'order': order})
