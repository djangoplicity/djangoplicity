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
from django.shortcuts import render
from djangoplicity.archives.contrib.satchmo.freeorder.forms import FreeOrderForm


def free_order_request( request ):
    if request.method == 'POST':
        try:
            form = FreeOrderForm( request.POST )
            if form.is_valid():
                form.save()
                return render(request, 'shop/freeorder_done.html', {'SHOP_BASE': settings.SATCHMO_SETTINGS['SHOP_BASE']})
        except ValueError:
            pass
    else:
        form = FreeOrderForm()

    return render(
        request,
        'shop/freeorder.html',
        {
            'form': form,
            'captcha_public_key': settings.RECAPTCHA_PUBLIC_KEY,
        },
    )
