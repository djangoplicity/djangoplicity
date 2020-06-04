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

from django.test import TestCase

#test all the models
from djangoplicity.menus.models import Menu, build_menu


class DeleteMenuItemBugTestCase( TestCase ):
    fixtures = [ 'menu_bug.json' ]

    def test_delete_menuitem(self):
        # First get the menu
        menu = Menu.objects.get( name__exact='Main menu' )
        menuroot = menu.menuitem_set.filter( level__exact=0 )[0]
        menuitems = menuroot.get_descendants()

        # Ensure we have a proper MPTT tree first
        self.assertEqual( len( menuitems ), 4 )
        self.assertEqual( menuroot.lft, 1 )
        self.assertEqual( menuroot.rght, 10 )
        self.assertEqual( menuitems[0].lft, 2 )
        self.assertEqual( menuitems[0].rght, 7 )
        self.assertEqual( menuitems[1].lft, 3 )
        self.assertEqual( menuitems[1].rght, 6 )
        self.assertEqual( menuitems[2].lft, 4 )
        self.assertEqual( menuitems[2].rght, 5 )
        self.assertEqual( menuitems[3].lft, 8 )
        self.assertEqual( menuitems[3].rght, 9 )

        # Delete the item
        menuitems[1].delete()

        # Verify the new tree
        menu = Menu.objects.get( name__exact='Main menu' )
        menuroot = menu.menuitem_set.filter( level__exact=0 )[0]
        menuitems = menuroot.get_descendants()

        self.assertEqual( len( menuitems ), 2 )
        self.assertEqual( menuroot.lft, 1 )
        self.assertEqual( menuroot.rght, 6 )
        self.assertEqual( menuitems[0].lft, 2 )
        self.assertEqual( menuitems[0].rght, 3 )
        self.assertEqual( menuitems[1].lft, 4 )
        self.assertEqual( menuitems[1].rght, 5 )


class RecursionBugTestCase( TestCase ):
    fixtures = [ 'recursion_bug.json' ]

    def test_build_menu( self ):
        """
        Testing a bug where the urls.sort() method in the end of build_menu
        reached maximum recursion depth when comparing list elements. Each list
        element is a two-tuple, where we actually only want to sort on the first
        element in the tuple (the URL), but where sorting on both elements.
        """
        build_menu( 'Main menu' )
