# -*- coding: utf-8 -*-
#
# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

from builtins import str
from builtins import range
from django.utils.translation import gettext as _
from datetime import datetime, timedelta
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db import models
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from six import python_2_unicode_compatible
from product.models import Discount, ProductAttribute
import string
import random

import django
if django.VERSION >= (2, 0):
    from django.urls import reverse
else:
    from django.core.urlresolvers import reverse

REJECT_REASONS = (
    ("NOSTOCK", "The product(s) is/are not available on stock."),
    ("UNQUALIFIED", "You did not qualify for receiving free orders at this occasion."),
    ("INSUFFICIENT", "Your justification is not sufficient to evaluate the request."),
    ("AMOUNT", "Your order was above our maximum of 180 EUR."),
    ("OLDCUSTOMER", "You already received a free order during the last six months"),
    ("ESONONLY", "Unfortunately we no longer ship free orders outside ESO Member States and host country Chile: https://www.eso.org/public/about-eso/memberstates/"),
    ("EUROONLY", "Unfortunately we no longer ship free orders outside Europe."),
    ("BUSY", "Due to an increase in demand, we were not able to accept your request at this time."),
)


def validate_percentage(val):
    if val < 0.0 or val > 100.0:
        raise ValidationError('Not a valid percentage.')


@python_2_unicode_compatible
class FreeOrder (models.Model):
    name = models.CharField(verbose_name='Full Name', max_length=250, blank=False)
    email = models.EmailField(verbose_name='Email Address', max_length=250, blank=False)
    country = models.ForeignKey('l10n.Country', verbose_name='Country of delivery', blank=False, on_delete=models.CASCADE)
    justification = models.TextField( verbose_name=_("Justification"), blank=False, help_text=_("Please tell us a few words about yourself/your organisation and provide a short justification explaining how you intend to use the products.") )

    accepted = models.NullBooleanField(verbose_name='Accepted')
    amount = models.FloatField( verbose_name='Discount percentage offered', null=False, validators=[validate_percentage], default=100.00 )
    discount_code = models.CharField(max_length=20, default='', blank=True, help_text='Created automatically.')

    reject_reason = models.CharField( max_length=255, blank=True, choices=REJECT_REASONS )

    submitted = models.DateTimeField(null=False)
    reviewed = models.DateTimeField(blank=True, null=True, help_text="Updated automatically.")

    class Meta:
        verbose_name = _("free order application")

    def __str__(self):
        return u"Free order application from %s" % self.name

    def clean(self):
        if self.accepted is not None and self.accepted is False and self.reject_reason == "":
            raise ValidationError("Please provide a rejection reason.")

    def send_email(self):
        from satchmo_store.shop.models import Config
        shop = Config.objects.get_current()
        site = Site.objects.get_current()

        # Generate discount code
        if self.accepted is True:
            self.create_code()  # 'DISCOUNT_CODE'
        else:
            self.delete_code()

        # Setup variables
        from_email = shop.store_email
        to = self.email
        subject = "%s - Free order application %s" % ( shop.store_name, "approved" if self.accepted else "rejected" )
        html_body = render_to_string( 'shop/freeorder_email.html', { 'order': self, 'shop': shop, 'site_url': site.domain } )
        text_body = strip_tags( html_body )

        # Send
        if subject and html_body and from_email:
            msg = EmailMultiAlternatives( subject, text_body, from_email, [to] )
            msg.attach_alternative( html_body, 'text/html' )
            msg.send()

        return

    def _code_build(self):
        return 'F-' + ''.join( random.choice( string.ascii_uppercase + string.digits ) for x in range( 6 ) )

    def create_code(self):

        discounts = Discount.objects.all()

        code = self._code_build()

        while len(discounts.filter(code=code)):
            #print "found matching code %s" % code
            code = self._code_build()

        d = Discount()
        d.site = Site.objects.all()[0]
        d.description = u"Discount for %s" % self.name
        d.code = code
        d.active = True
        d.percentage = 100
        d.allowedUses = 1
        d.allValid = False
        d.startDate = datetime.now()
        d.endDate = datetime.now() + timedelta(days=30)
        d.shipping = 'FREE'
        d.save()

        # All free products
        for p in ProductAttribute.objects.filter( option__name='Free', value="YES" ):
            d.valid_products.add( p.product )

        d.save()

        self.discount_code = code
        return code

    def rebuild_free_products(self):
        if self.accepted:
            try:
                d = Discount.objects.get( code=self.discount_code )
                d.valid_products.all().delete()

                for p in ProductAttribute.objects.filter( option__name='Free', value="YES" ):
                    d.valid_products.add( p.product )

                d.save()
            except Discount.DoesNotExist:
                pass

    def delete_code(self):
        if self.discount_code:
            try:
                d = Discount.objects.get(code=self.discount_code)
                d.delete()
            except Discount.DoesNotExist:
                pass
        self.discount_code = ''

    def delete(self, *args, **kwargs):
        self.delete_code()
        super(FreeOrder, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        """ We override save to check for value transition on accepted/rejected """

        # Send notification for new submissions
        new = False
        if self.pk is None:
            new = True

        # get old order
        try:
            old_order = FreeOrder.objects.get(pk=self.pk)
            if old_order.accepted != self.accepted and self.accepted is not None:
                self.reviewed = datetime.now()
                self.send_email()
        except FreeOrder.DoesNotExist:
            self.submitted = datetime.now()

        super(FreeOrder, self).save(*args, **kwargs)

        if new:
            from satchmo_store.shop.models import Config
            # Send email to Oana for confirmation
            shop = Config.objects.get_current()
            from_email = shop.store_email
            to = ['osandu@partner.eso.org']
            subject = "%s - Free order application submitted" % shop.store_name
            text_body = '''
%s submitted a free order application.

Email: %s
Justification:
%s

https://%s%s
''' % (self.name, self.email, self.justification,
        Site.objects.get_current().domain, reverse('adminshop_site:freeorder_freeorder_change', args=[str(self.pk)]))

            send_mail(subject, text_body, from_email, to)

            # Send confirmation email to requester
            to = [self.email]
            subject = "%s - Free order application submitted" % shop.store_name
            text_body = '''
Dear %s,

Thank you for your message! Your free order request is being processed
and you will receive an answer in the coming 10 working days.
''' % self.name

            send_mail(subject, text_body, from_email, to)
