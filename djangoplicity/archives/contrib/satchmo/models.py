# -*- coding: utf-8 -*-
#
# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

"""
"""

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from djangoplicity.archives.contrib.satchmo.listeners import newsletter_form_listener, newsletter_form_listener_init, pay_ship_form_init, contact_reset_listener
from payment.forms import PaymentContactInfoForm, SimplePayShipForm
from payment.listeners import form_terms_listener
from product.models import Product, AttributeOption, ProductAttribute, Price, \
    Category
from satchmo_store.shop.signals import rendering_store_mail, sending_store_mail, order_success
from signals_ahoy.signals import form_init, form_postsave

import re

DEFAULT_JOB_NO = settings.SHOP_CONF['DEFAULT_NAVISION_JOB'] if hasattr( settings, 'SHOP_CONF' ) else ''
DEFAULT_JSP_NO = settings.SHOP_CONF['DEFAULT_NAVISION_JSP'] if hasattr( settings, 'SHOP_CONF' ) else None
DEFAULT_ACCOUNT_NO = settings.SHOP_CONF['DEFAULT_NAVISION_ACCOUNT'] if hasattr( settings, 'SHOP_CONF' ) else ''
ARCHIVE_DEFAULTS = settings.SHOP_CONF['ARCHIVE_DEFAULTS'] if hasattr( settings, 'SHOP_CONF' ) else {}
DEFAULT_FREE = False


# the purpose of these functions is to mask the parameters from django migrations
def DEFAULT_JOB_NO_HELP_TEXT_FUNC(job_no=DEFAULT_JOB_NO):
    return _( 'Navision job no. - if left blank, the current default job no %s is used' ) % job_no


def DEFAULT_JSP_NO_FUNC(jsp_no=DEFAULT_JSP_NO):
    return _( 'Navision JSP no. - if left blank, the current default JSP no %s is used' ) % jsp_no


def DEFAULT_ACCOUNT_NO_FUNC(account_no=DEFAULT_ACCOUNT_NO):
    return _( 'Navision account no. - if left blank, the current default account no %s is used' ) % account_no


def _defaults( cls ):
    """
    Get the default job, JSP and account for an archive.
    """
    defaults = { 'JOB': DEFAULT_JOB_NO, 'JSP': DEFAULT_JSP_NO, 'ACCOUNT': DEFAULT_ACCOUNT_NO, }
    try:
        archive_defaults = ARCHIVE_DEFAULTS["%s.%s" % ( cls.__module__, cls.__name__ )]
        defaults.update( archive_defaults )
    except KeyError:
        pass

    return defaults


def product_archive_item( product ):
    """
    Retrieve the archive item from a Satchmo product.
    First matching archive object will be retrieved.
    """

    # The subtype is stored in the SKU, we use it to identify
    # which DJP product to query as this requires much less queries
    # than looping on all possible subtypes
    subtype = product.sku.split(':')[0]
    try:
        return getattr(product, subtype)
    except AttributeError:
        return None


class ShopModel( models.Model ):
    """
    Abstract class containing shop-related information across all archives
    """
    # Sell archive item in webshop?
    sale = models.BooleanField( default=False, help_text=_( u'For sale - note weight must be provided if product is for sale.' ) )

    # Price of the product
    price = models.DecimalField( default="0.00", max_digits=8, decimal_places=2, help_text=_( u'Price (EUR)' ) )

    # Relation to the Satchmo product in the webshop
    product = models.OneToOneField( Product, on_delete=models.SET_NULL, null=True, blank=True )

    # Navision job no.
    job = models.CharField( max_length=4, blank=True, help_text=DEFAULT_JOB_NO_HELP_TEXT_FUNC )

    # Navision JSP no.
    jsp = models.IntegerField( verbose_name=_( 'JSP' ), null=True, blank=True, help_text=DEFAULT_JSP_NO_FUNC )

    # Navision account no.
    account_no = models.CharField( max_length=10, blank=True, help_text=DEFAULT_ACCOUNT_NO_FUNC )

    # Item is for free
    free = models.BooleanField( null=False, default=False, verbose_name="Free", help_text=_( "Available for free." ) )

    shippable = models.BooleanField( default=True, help_text=_( "Calculate shipping for this item." ) )
    #   Determine if product are shippable.

    def satchmo_slug( self ):
        """
        Return an id for the archive item, that doesn't conflict with other archives
        """
        return self.id

    def satchmo_sku( self ):
        """
        Return a SKU for the archive item, that doesn't conflict with other archives
        """
        return "%s::%s" % ( self._get_subtype().lower(), self.id )

    def update_product( self, product ):
        """
        Helper method that allows the archive item to select what to put into the product.

        Must return the product
        """
        product.site = Site.objects.get_current()
        product.slug = self.satchmo_slug()
        product.sku = self.satchmo_sku()
        product.weight = self.weight
        product.weight_units = 'g'
        product.active = self.published
        # Products IDs should be under the form category_id and archive
        # products are ordered by IDs, to match the ordering we extract the id
        # from the product if it matches the expected format:
        match = re.match(r'\w+_(\d+)', self.id)
        if match:
            # We use 1000 - id as the Shop product are ordered by increasing
            # ordering
            product.ordering = 1000 - int(match.group(1))
        else:
            # Use default ordering
            product.ordering = 100 - self.priority
        product.name = self.title
        product.description = self.description
        if self.shippable:
            product.shipclass = 'YES'
        else:
            product.shipclass = 'NO'

        return product

    def update_categories( self, product, add=True ):
        """
        Helper method for allowing the archive item to decide which categories to
        include the product in.

        Called after the product including price and attributes have been created.

        Must return a list of categories created or added to product.
        """
        try:
            category = Category.objects.get( site=Site.objects.get_current(), slug=self._get_subtype().lower() )
        except Category.DoesNotExist:
            category = Category( site=Site.objects.get_current(), slug=self._get_subtype().lower(), name=unicode( self._meta.verbose_name_plural ).title() )
            category.save()

        if add:
            product.category.add( category )

        return [category]

    def update_price( self, product ):
        """
        Helper method for setting the price of the product.
        """
        try:
            # For existing or modified products
            price = Price.objects.filter( product=product, quantity='1.0', expires__isnull=True ).get()
            price.price = self.price
        except Price.DoesNotExist:
            # For new products
            price = Price( product=product, price=self.price )
        price.save()

    def update_attributes( self, product ):
        """
        Helper method for setting attributes on the product
        """
        # Get product attribute options, or create them if they don't exists.
        try:
            job_attr_opt = AttributeOption.objects.get( name='Job' )
        except AttributeOption.DoesNotExist:
            job_attr_opt = AttributeOption( name='Job', description='Job', validation='product.utils.validation_simple' )
            job_attr_opt.save()

        try:
            jsp_attr_opt = AttributeOption.objects.get( name='JSP' )
        except AttributeOption.DoesNotExist:
            jsp_attr_opt = AttributeOption( name='JSP', description='JSP', validation='product.utils.validation_integer' )
            jsp_attr_opt.save()

        try:
            account_attr_opt = AttributeOption.objects.get( name='Account' )
        except AttributeOption.DoesNotExist:
            account_attr_opt = AttributeOption( name='Account', description='Account', validation='product.utils.validation_simple' )
            account_attr_opt.save()

        try:
            free_attr_opt = AttributeOption.objects.get( name='Free' )
        except AttributeOption.DoesNotExist:
            free_attr_opt = AttributeOption( name='Free', description='For Free', validation='product.utils.validation_yesno' )
            free_attr_opt.save()

        job_attr = ProductAttribute.objects.get_or_create( product=product, option=job_attr_opt )[0]
        job_attr.value = unicode( self.job if self.job else self.default_job() )
        job_attr.save()

        jsp_attr = ProductAttribute.objects.get_or_create( product=product, option=jsp_attr_opt )[0]
        jsp_attr.value = unicode( self.jsp if self.jsp else self.default_jsp() )
        jsp_attr.save()

        account_attr = ProductAttribute.objects.get_or_create( product=product, option=account_attr_opt )[0]
        account_attr.value = unicode( self.account_no if self.account_no else self.default_account_no() )
        account_attr.save()

        free_attr = ProductAttribute.objects.get_or_create( product=product, option=free_attr_opt )[0]
        free_attr.value = unicode( 'YES' if self.free else 'NO' )
        free_attr.save()

    def clean( self ):
        """
        Validate that the we have a valid weight
        """
        # Products on sale must provide a weight
        if self.sale:
            if not hasattr( self, "weight" ):
                raise ValidationError( "Djangoplicity internal setup problem - archive item doesn't have a weight attribute that the shop relies on for shipping calculations." )

            try:
                int( self.weight )
            except ValueError:
                raise ValidationError( "Please provide a weight in gram for this item (used for shipping calculations)." )

    @classmethod
    def post_delete_handler( cls, sender, instance, **kwargs ):
        """
        Post-delete handler for creating/updating product related to archive item.
        """
        pass
        # Wed 30 Jan 16:54:24 CET 2019 - Mathias
        # This used to delete the shop products, but this causes problems
        # if orders exist with this product, so we just ignore the shop product
        #  if instance.product:
        #      instance.product.delete()

    @classmethod
    def post_save_handler( cls, sender, instance, created, raw=True, **kwargs ):
        """
        Post-save signal handler for creating/updating product related to archive item.

        Noteworthy:
            * Archive item data overwrites product data (no sync)
            * get_subtype() on archive is used with item id to generate slug for product.
            * Category for archive is automatically created if it doesn't exists (verbose_name_plural is used as title)
            * Category title can be changed via admin - and will not be overwritten. Category slug however cannot be changed.
            * Product is only active if archive item is published and sale=yes.
            * Only the price for 1 item is written - hence, quantity discount can be given and will not be overwritten.
        """
        if raw:
            return

        # Prevent that signal is invoked when we're just saving the product id on the archive item
        if not getattr( instance, '_updating_product_state', False ):
            if instance.sale:
                if instance.product:
                    p = instance.product
                else:
                    p = Product()

                # Update product (TODO: weight)

                # Let archive item update product and save.
                p = instance.update_product( p )

                # Save product
                p.save()

                # Set product on archive item, if not already set
                if not instance.product:
                    instance.product = p
                    instance._updating_product_state = True
                    instance.save()
                    del instance._updating_product_state

                # Set price on product
                instance.update_price( p )

                # Save product attributes (e.g. Job/JSP no)
                instance.update_attributes( p )

                # Add categories for product
                instance.update_categories( p )

            elif not instance.sale and instance.product:
                p = instance.product
                p.active = False
                p.save()

    class Meta:
        abstract = True

    @classmethod
    def default_job( cls ):
        return _defaults( cls )['JOB']

    @classmethod
    def default_jsp( cls ):
        return _defaults( cls )['JSP']

    @classmethod
    def default_account_no( cls ):
        return _defaults( cls )['ACCOUNT']


def modify_subject( sender, send_mail_args=None, context=None, **kwargs ):
    """
    Modify the subject of the emails send by Satchmo to include the order id.
    """
    if send_mail_args is None:
        send_mail_args = {}
    if context is None:
        context = {}
    if 'order' not in context:
        return

    orderid = context['order'].get_variable('ORDER_ID').value
    send_mail_args['subject'] = send_mail_args['subject'] + ' - %s' % orderid


def modify_mail_context( sender, send_mail_args=None, context=None, **kwargs ):
    """
    Modify mail context by adding the shop config as a template variable.
    """
    if send_mail_args is None:
        send_mail_args = {}
    if context is None:
        context = {}
    if 'shop' in context:
        return

    from satchmo_store.shop.models import Config
    shop_config = Config.objects.get_current()
    site_domain = Site.objects.get_current().domain

    context['shop'] = shop_config
    context['site_domain'] = site_domain


# Connect listeners to signals.
sending_store_mail.connect( modify_subject )
rendering_store_mail.connect( modify_mail_context )
form_init.connect( form_terms_listener, sender=PaymentContactInfoForm )
form_init.connect( newsletter_form_listener_init, sender=PaymentContactInfoForm )
form_init.connect( pay_ship_form_init, sender=SimplePayShipForm )
form_postsave.connect( newsletter_form_listener, sender=PaymentContactInfoForm )
order_success.connect( contact_reset_listener )
