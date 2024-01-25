# -*- coding: utf-8 -*-
#
# djangoplicity-media
# Copyright (c) 2007-2011, European Southern Observatory (ESO)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the European Southern Observatory nor the names
#      of its contributors may be used to endorse or promote products derived
#      from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY ESO ``AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL ESO BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE

from __future__ import division
from past.utils import old_div
from django import template
from django.utils.html import mark_safe
import math

register = template.Library()

units = [(0, 'nm'), (3, '&mu;m'), (6, 'mm'), (7, 'cm'), (9, 'm')]


def power10( x, p ):
    if x >= 10:
        return power10( old_div(x, 10), p + 1 )
    else:
        return p


@register.filter(is_safe=True)
def wavelength( l ):
    """
    Format a wavelength given in nanometers.
    """
    try:
        if not l:
            return ""
        # Initialization
        l = float( l )
        l_p, l_txt = ( 0, 'nm' )

        # Find the power of 10 so base is between 1 and 10
        p = power10( l, 0 )

        # Find appropriate unit
        for ( unit_p, unit_txt ) in units:
            if p >= unit_p:
                l_p, l_txt = (unit_p, unit_txt)
            else:
                break

        # Convert l to determine unit
        l = old_div(l, math.pow( 10, l_p ))

        # Only put digits on numbers below 10.
        if l >= 10:
            l = int( l )

        return mark_safe( "%s %s" % ( l, l_txt ) )
    except ValueError:
        return ""
