# -*- coding: utf-8 -*-
#
# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

import requests


from django import forms
from django.conf import settings

from djangoplicity.archives.contrib.satchmo.freeorder.models import FreeOrder

# from forms import FreeOrderForm
from djangoplicity.archives.contrib.satchmo.listeners import newsletter_form_listener


class FreeOrderForm (forms.ModelForm):
    if hasattr(settings, "SHOP_NEWSLETTER_FROM"):
        SHOP_NEWSLETTER_FROM = settings.SHOP_NEWSLETTER_FROM
    else:
        SHOP_NEWSLETTER_FROM = "ESO & ESA/Hubble"
    newsletter = forms.BooleanField(label='Yes, I want to receive a newsletter from %s' % SHOP_NEWSLETTER_FROM, widget=forms.CheckboxInput(), required=False, initial=True)

    class Meta:
        model = FreeOrder
        fields = ['name', 'email', 'country', 'justification']

    def clean(self):
        '''
        Verify captcha
        '''
        # Check that the captcha is valid
        payload = {
            'secret': settings.RECAPTCHA_PRIVATE_KEY,
            'response': self.data.get('g-recaptcha-response', ''),
        }

        r = requests.post('https://www.google.com/recaptcha/api/siteverify',
            data=payload, verify=False)
        # We don't verify the SSL as Google's SSL doesn't work currently
        # on media3/4

        if r.status_code == requests.codes.ok and r.json()['success']:
            return super(FreeOrderForm, self).clean()
        else:
            raise forms.ValidationError('Invalid captcha, please confirm that you are not a robot')

    def save(self, commit=True):
        newsletter_form_listener(self, form=self)
        super(FreeOrderForm, self).save(commit=commit)
