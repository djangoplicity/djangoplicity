import os

from celery.task import task

from django.conf import settings
from django.core.mail import send_mail


@task(ignore_result=True)
def report_shippable_no_weight( model_identifier=None ):
    """
    Celery task to identify shippable product with no weight
    """
    logger = report_shippable_no_weight.get_logger()
    logger.info('Searching for shippable products with no weight')

    from product.models import Product
    products = Product.objects.filter(active=True)

    products = [ p for p in products if p.is_shippable and not p.weight ]

    if not products:
        return

    from django.core.mail import EmailMessage
    from django.contrib.sites.models import Site

    domain = Site.objects.get_current().domain

    msg = EmailMessage()
    msg.from_email = settings.DEFAULT_FROM_EMAIL
    msg.to = ['epoddist@eso.org', ]
    msg.subject = 'Shippable products missing weight in shop'
    msg.body = '''Dear EpodDist,

Please set a weight for the following ESO Shop product, if the products
are not shippable set the 'Shipping' dropdown to 'Not Shippable' instead:

%s
''' % '\n'.join(['http://%s%s' % (domain, p.get_absolute_url()) for p in products])

    msg.send()


@task(ignore_result=True)
def shop_subscribers():
    '''
    Send an email to webteam with the list of shop subscribers
    that opted in for the newsletters
    '''
    path = os.path.join(settings.SHARED_DIR, 'shop-subscribers.txt')

    if not os.path.exists(path):
        return

    url = getattr(settings, 'NEWSLETTER_SUBSCRIBERS_URL', None)
    if url is None:
        return

    emails = open(path).read()
    body = '''
Please subscribe the following email addresses to: {url}

{emails}
    '''.format(url=url, emails=emails)

    send_mail(
        'Shop customers to subscribe to newsletter',
        body,
        'no-reply@eso.org',
        ['epodweb@eso.org'],
    )

    os.unlink(path)
