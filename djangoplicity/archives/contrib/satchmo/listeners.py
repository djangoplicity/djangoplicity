from product.signals import index_prerender
from product.models import Product
from django.template import loader
from django import forms
from django.conf import settings
from djangoplicity.archives.contrib.satchmo.esoshipping.utils import validate_order
import logging
import os

if hasattr( settings, "SHOP_NEWSLETTER_FROM"):
    SHOP_NEWSLETTER_FROM = settings.SHOP_NEWSLETTER_FROM
else:
    SHOP_NEWSLETTER_FROM = "ESO & ESA/Hubble"


def category_prerender( sender, request=None, context=None, category=None, brand=None, object_list=None, **kwargs ):
    """
    Add a variable to the context of the category template.
    """
    if category:
        slugs = [category.slug]
        while category.parent:
            category = category.parent
            slugs.insert( 0, category.slug )

        name = ""
        names = []
        for s in slugs:
            name += "_%s" % s
            names.append(name)

        templates = [ "site-specific/product/category%s.html" % n for n in names ]
        templates.append( "site-specific/product/category.html" )

        tmpl = loader.select_template( templates )
        context['base_template'] = tmpl

index_prerender.connect( category_prerender, sender=Product )


def newsletter_form_listener(sender, object=None, formdata=None, form=None, **kwargs):
    """
    Check if newsletter is in form data and subscribe user if he/she accepts.
    """
    if not form.data or (form.data and "newsletter" not in form.data):
        subscribed = False
    else:
        subscribed = form.data["newsletter"]

    if subscribed:
        if "email" in form.data:
            logger = logging.getLogger()
            logger.info( "Subscribe  %s", form.data["email"] )
            path = os.path.join(settings.SHARED_DIR, 'shop-subscribers.txt')
            f = open(path, 'a')
            f.write('%s\n' % form.data["email"])
            f.close()


def newsletter_form_listener_init( sender, form=None, **kwargs ):
    """
    Add's newsletter accept box to form
    """
    form.fields['newsletter'] = forms.BooleanField( label='Yes, I want to receive a newsletter from %s' % SHOP_NEWSLETTER_FROM, widget=forms.CheckboxInput(), required=False, initial=True )


def pay_ship_form_init( sender, form=None, **kwargs ):
    """
    Hide/show and pre-select shipping methods based on contact/order.

    Currently contacts with @eso.org address will only be able to choose
    office delivery, while office delivery will be hidden for everyone else.
    """
    #logger = logging.getLogger()
    #logger.info("Before choices: %s" % unicode([x[0] for x in form.fields['shipping'].choices]) )
    #logger.info("Before initial: %s" % unicode(form.fields['shipping'].initial) )

    # Create dictionary of shipping methods
    if form.order.is_shippable:
        shipdict = {}
        for (k, v) in form.fields['shipping'].choices:
            shipdict[k] = v

        if form.order and validate_order( form.order ):
            # ESO employee only shipping
            from djangoplicity.archives.contrib.satchmo.esoshipping.officedelivery.shipper import Shipper
            form.fields['shipping'].initial = Shipper.id
            form.fields['shipping'].choices = [( Shipper.id, shipdict[Shipper.id] )]
        else:
            form.fields['shipping'].initial = 'tieredweight_1'

    #logger.info("After choices: %s" % unicode([x[0] for x in form.fields['shipping'].choices]) )
    #logger.info("After initial: %s" % unicode(form.fields['shipping'].initial) )


def contact_reset_listener( sender, **kwargs ):
    """
    Make sure a customer who successfully placed an order
    gets the customer id cleared from the session.

    This solves the problem that a secretary orders several
    conference fess for persons, and that on each order
    the basic information is overwritten.
    """
    from threaded_multihost import threadlocals
    from satchmo_store.contact import CUSTOMER_ID
    session = threadlocals.get_current_session()
    if session:
        try:
            del session[CUSTOMER_ID]
        except KeyError:
            pass
