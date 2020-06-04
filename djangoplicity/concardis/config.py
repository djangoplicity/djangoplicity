from livesettings.functions import config_register_list
from livesettings.values import ConfigurationGroup, StringValue, BooleanValue, \
    ModuleValue
from django.utils.translation import ugettext_lazy as _

PAYMENT_GROUP = ConfigurationGroup('PAYMENT_CONCARDIS',
    _('Concardis Payment Module Settings'),
    ordering=101)

config_register_list(

StringValue(PAYMENT_GROUP,
    'CURRENCY_CODE',
    description=_('Currency Code'),
    help_text=_('Currency code for Concardis transactions.'),
    default='EUR'),

StringValue(PAYMENT_GROUP,
    'SHA_IN_PASSPHRASE',
    description=_('SHA-IN pass phrase'),
    help_text=_('The SHA-IN pass phrase used to hash the parameters.'),
    default=''),

StringValue(PAYMENT_GROUP,
    'SHA_OUT_PASSPHRASE',
    description=_('SHA-OUT pass phrase'),
    help_text=_('The SHA-OUT pass phrase used to hash the parameters.'),
    default=''),

StringValue(PAYMENT_GROUP,
    'POST_URL',
    description=_('Post URL'),
    help_text=_('The Concardis URL for real transaction posting.'),
    default='https://secure.payengine.de/ncol/prod//orderstandard_utf8.asp'),

StringValue(PAYMENT_GROUP,
    'POST_TEST_URL',
    description=_('Test Post URL'),
    help_text=_('The Concardis URL for test transaction posting.'),
    default='https://secure.payengine.de/ncol/test//orderstandard_utf8.asp'),

StringValue(PAYMENT_GROUP,
    'PSPID',
    description=_('Concardis PSPID'),
    help_text=_('The PSPID for your Concardis account'),
    default=''),

StringValue(PAYMENT_GROUP,
    'RETURN_ADDRESS',
    description=_('Return URL'),
    help_text=_('Where Concardis will return the customer after the purchase is complete.  This can be a named url and defaults to the standard checkout success.'),
    default='satchmo_checkout-success'),

BooleanValue(PAYMENT_GROUP,
    'LIVE',
    description=_('Accept real payments'),
    help_text=_('False if you want to be in test mode'),
    default=False),

ModuleValue(PAYMENT_GROUP,
    'MODULE',
    description=_('Implementation module'),
    hidden=True,
    default='djangoplicity.concardis'),

StringValue(PAYMENT_GROUP,
    'KEY',
    description=_('Module key'),
    hidden=True,
    default='CONCARDIS'),

StringValue(PAYMENT_GROUP,
    'LABEL',
    description=_('English name for this group on the checkout screens'),
    default='Concardis',
    dummy=_('Concardis'),  # Force this to appear on po-files
    help_text=_('This will be passed to the translation utility')),

StringValue(PAYMENT_GROUP,
    'URL_BASE',
    description=_('The url base used for constructing urlpatterns which will use this module'),
    default='^payment/'),

BooleanValue(PAYMENT_GROUP,
    'EXTRA_LOGGING',
    description=_('Verbose logs'),
    help_text=_('Add extensive logs during post.'),
    default=False)
)

PAYMENT_GROUP['TEMPLATE_OVERRIDES'] = {
    'shop/checkout/confirm.html': 'shop/checkout/concardis/confirm.html',
}
