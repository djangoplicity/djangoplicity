from __future__ import unicode_literals
import hashlib
from collections import OrderedDict

from django.utils.http import urlunquote_plus


TRANSACTION_STATUSES = {
    '0': '0 - Invalid or incomplete',
    '1': '1 - Cancelled by customer',
    '2': '2 - Authorisation refused',
    '4': '4 - Order stored',
    '40': '40 - Stored waiting external result',
    '41': '41 - Waiting for client payment',
    '46': '46 - Waiting authentication',
    '5': '5 - Authorised',
    '50': '50 - Authorized waiting external result',
    '51': '51 - Authorisation waiting',
    '52': '52 - Authorisation not known',
    '55': '55 - Standby',
    '56': '56 - Ok with scheduled payments',
    '57': '57 - Not OK with scheduled payments',
    '59': '59 - Authorization to be requested manually',
    '6': '6 - Authorised and cancelled',
    '61': '61 - Author. deletion waiting',
    '62': '62 - Author. deletion uncertain',
    '63': '63 - Author. deletion refused',
    '64': '64 - Authorised and cancelled',
    '7': '7 - Payment deleted',
    '71': '71 - Payment deletion pending',
    '72': '72 - Payment deletion uncertain',
    '73': '73 - Payment deletion refused',
    '74': '74 - Payment deleted',
    '8': '8 - Refund',
    '81': '81 - Refund pending',
    '82': '82 - Refund uncertain',
    '83': '83 - Refund refused',
    '84': '84 - Refund',
    '85': '85 - Refund handled by merchant',
    '9': '9 - Payment requested',
    '91': '91 - Payment processing',
    '92': '92 - Payment uncertain',
    '93': '93 - Payment refused',
    '94': '94 - Refund declined by the acquirer',
    '95': '95 - Payment handled by merchant',
    '96': '96 - Refund reversed',
    '99': '99 - Being processed',
}


def sha1_sign(params, passphrase):
    '''
    Returns a sha1 digest of the params dictionnary.
    Params is concatenated with the passphrase
    '''
    # Make sure params are sorted alphabetically
    params = OrderedDict(sorted(params.items(), key=lambda t: t[0]))

    string = ''.join([
        '{}={}{}'.format(key, val, passphrase)
        for (key, val) in params.items()
        if val  # Empty values are not included in the hash
    ]).encode('utf-8')  # Encode to utf-8 as hashlib expects byte string

    return hashlib.sha1(string).hexdigest().upper()


def get_params(request):
    '''
    Build a dictionary with the URL parameters
    '''
    return dict([
        (key.upper(), urlunquote_plus(val))
        for key, val in request.GET.items()
        if key.upper() != 'SHASIGN'
    ])


def get_payment_status(params):
    '''
    Return the short and long string version of the 'STATUS' parameter if available
    '''
    key = 'STATUS'
    if key not in params:
        return ('', 'No "{}" in received parameters'.format(key))

    try:
        return (params[key], TRANSACTION_STATUSES[params[key]])
    except KeyError:
        return (params[key], '')
