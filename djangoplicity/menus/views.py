# -*- coding: utf-8 -*-
#
# djangoplicity-menus
# Copyright (c) 2007-2011, European Southern Observatory (ESO)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#
#   * Neither the name of the European Southern Observatory nor the names
#     of its contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
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


from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache
from djangoplicity.menus.models import MenuItem, invalidate_menu_item_cache


def sitemap( request ):
    """ Render a sitemap """
    return render(request, 'menus/sitemap.html')


@staff_member_required
@never_cache
def moveup(request, menuitem ):
    """ TODO: quite big hack """
    item = get_object_or_404( MenuItem, id=menuitem )
    #if item.get_previous_sibling():
    item.move_to(item.get_previous_sibling(), 'left' )
    invalidate_menu_item_cache( None, item, None )

    return HttpResponseRedirect(reverse('admin:menus_menuitem_changelist', current_app='admin_site'))


@staff_member_required
@never_cache
def movedown(request, menuitem ):
    """ TODO: quite big hack """
    item = get_object_or_404( MenuItem, id=menuitem )
    #if item.get_next_sibling():
    item.move_to(item.get_next_sibling(), 'right' )
    invalidate_menu_item_cache( None, item, None )

    return HttpResponseRedirect(reverse('admin:menus_menuitem_changelist', current_app='admin_site'))
