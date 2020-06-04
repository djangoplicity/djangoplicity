# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from django.conf import settings
from django.shortcuts import render

from djangoplicity.media.models import Video


def fb_welcome( request ):

    video1 = Video.objects.get(id='esotrailer')

    return render(request, 'iframe/welcome.html', {
        'video1': video1,
        'override_size': '150',
        'wall_url': settings.SOCIAL_FACEBOOK_WALL,
    })


def fb_discoveries( request ):

    video1 = None  # Video.objects.get(id='esotrailer')

    return render(request, 'iframe/discoveries.html', {
        'video1': video1,
        'override_size': '150',
        'wall_url': settings.SOCIAL_FACEBOOK_WALL
    })


def fb_virtualtours( request ):

    video1 = None  # Video.objects.get(id='esotrailer')

    return render(request, 'iframe/virtualtours.html', {
        'video1': video1,
        'override_size': '150',
        'wall_url': settings.SOCIAL_FACEBOOK_WALL
    })
