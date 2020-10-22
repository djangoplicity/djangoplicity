# -*- coding: utf-8 -*-
#
# djangoplicity-menus
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

from builtins import str
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import signals
from django.utils import translation
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
from djangoplicity.translation.models import get_path_for_language, get_language_from_path
from mptt.models import MPTTModel
from operator import itemgetter

CACHE_KEY = 'djangoplicity.menus.menu_'

CLICK_OPTIONS = (
    ( 0, _( u'Same window' ) ),
    ( 1, _( u'New window' ) ),
)


class MenuDoesNotExist(Exception):
    """ Exception to signal that a menu does not exists. """
    pass


@python_2_unicode_compatible
class Menu( models.Model ):
    """
    A menu groups a list of menu items.
    """

    # Name of the menu
    name = models.CharField( max_length=100, unique=True )

    # A menu always have exactly one menu root. This option defines if the
    # root menu item should be shown.
    hide_menu_root = models.BooleanField( default=True, help_text=_( u'Defines if the root menu item should be hidden (a menu always have exactly one root menu item).' ) )

    # Defines the default expansion level of the menu. Use e.g. 2 to show
    # the first two levels in the menu. A value of 0 shows the entire menu.
    # This field can be overridden by the template.
    expansion_depth = models.PositiveSmallIntegerField( default=0, help_text=_( u'Defines the default expansion level of the menu. Use e.g. 2 to show the first two levels in the menu. A value of 0 shows the entire menu. This field can be overridden by the template.' ) )

    # Defines the maximum number of levels allowed in the menu. A value
    # of 0 means no limits. This field can be overridden by the template.
    max_depth = models.PositiveSmallIntegerField( default=0, help_text=_( u'Defines the maximum number of levels allowed in the menu. A value of 0 means no limits. This field can be overridden by the template.' ) )

    def __str__( self ):
        """ """
        return self.name

    class Meta:
        ordering = ( 'name', )


@python_2_unicode_compatible
class MenuItem( MPTTModel ):
    """
    Registered as Modified Preorder Tree Traversal (MPTT) model. See documentation of Django MPTT
    for more information about added model instance methods.
    """

    # The title of the menu item
    title = models.CharField( max_length=100 )

    # URL for the menu item.
    link = models.CharField( max_length=255, blank=True, help_text=_( u'Use lower-case letters only. Local links should start with forward slash, and normally ends with slash - eg /science/. Remote links should be full URLs - eg http://www.cnn.com/. The field can be left empty, in which case the menu item won\'t be linked.' ) )

    # TODO: FIELD CURRENTLY HAS NO EFFECT
    published = models.BooleanField( default=True )

    # Action to use when clicking the link
    on_click = models.PositiveIntegerField( default=0, choices=CLICK_OPTIONS )

    # The root menu item, must be related to a menu.
    menu = models.ForeignKey( Menu, blank=True, null=True, help_text=_( u'This field only have effect for the root menu item'), on_delete=models.CASCADE)

    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', help_text=_( u'Moving a node to a new parent, will place it as the last node. When moving a menu item, all of it sub-items will be moved as well.'), on_delete=models.CASCADE)

    # Indicates that this is the primary menu item, for a given URL.
    # In case a menu contains several items with the same link, set
    # this field to true and the others menu items field to false, to
    # control which item is used for item highlighting and breadcrumb
    # generation.
    is_primary = models.BooleanField( default=True, help_text=_( u'In case a menu contains several items with the same link, set this field to true and the others menu items field to false, to control which item is used for item highlighting and breadcrumb generation.') )

    def __str__( self ):
        return self.title

    class Meta:
        ordering = [ 'tree_id', 'lft' ]


class MenuProxy:
    """
    Proxy object for cached menus. Can be used to
    """
    def __init__(self, menu_name):
        self.menu_name = menu_name
        self.menu = None

    def get_menu(self):
        """
        Retrieve menu that this object is proxy for. One this method is called
        the actual menu will be retrieve from cache, or generated if not
        in the cache.
        """
        if self.menu is None:
            # get_menu is not the instance method, but normal method.
            self.menu = get_menu( self.menu_name )

        return self.menu


def build_menu( name ):
    """
    Build a menu data structure given a flat (but structure-ordered) list
    of menu items. Also builds a url index, mapping urls in the menu
    to its corresponding menu items.
    """
    try:
        # First get the menu
        menu = Menu.objects.get( name__exact=name )

        # Note a menu should only have one tree structure, thus
        # we take the first element of all menu items related to
        # the menu. Level_attr=0
        menuroot = menu.menuitem_set.filter( level__exact=0 )[0]
        menuitems = menuroot.get_descendants()

        i = 1

        # Create the structure of the menu from a flat list,
        # by use of a stack.
        root = {
            'title': menuroot.title,
            'link': menuroot.link,
            'published': menuroot.published,
            'on_click': menuroot.on_click,
            'expand': menu.expansion_depth >= menuroot.level,
            'selected': False,
            'leaf_selected': False,
            'children': [],
            'parent': None,
            'level': 0,
            'hide_menu_root': menu.hide_menu_root,
            'id': i
        }

        # Initialize stacks and state variables.
        parent_stack = []
        previous_level = 1
        parent = root
        children = root['children']
        urls = []

        skipping_children = False
        current_item = None
        skip_level = None
        for item in menuitems:
            if skipping_children:
                if item.level > skip_level:
                    continue
                else:
                    skipping_children = False

            if not item.published:
                skipping_children = True
                skip_level = item.level
                continue

            i += 1

            if previous_level < item.level:
                # Structure is going a level down
                parent[ 'children' ] = children
                parent_stack.append( parent )
                parent = current_item
                children = parent['children']
            elif previous_level > item.level:

                # Structure is going *one or possibly more*  levels up

                # Remove parents from stack, in case we went *more than one*
                # level up. If we went just *one* level up, following two
                # statements has no effect.
                pop = parent['level'] - item.level
                del parent_stack[len(parent_stack) - pop:]

                # Pop parent from stack, and get children
                parent = parent_stack.pop()
                children = parent[ 'children' ]

            # Append current item to list of children.
            current_item = {
                'title': item.title,
                'link': item.link,
                'published': item.published,
                'on_click': item.on_click,
                'expand': menu.expansion_depth >= item.level,
                'selected': False,
                'leaf_selected': False,
                'children': [],
                'parent': parent,
                'level': item.level,
                'id': i
            }
            children.append( current_item )

            # Index item by URL if not URL is already in index
            if item.is_primary:
                urls.append( (item.link, current_item) )
            previous_level = item.level

        # If we don't hide the menu root we include it so that it can also
        # appear in the breadcrumb and menu
        if not menu.hide_menu_root:
            current_item = {
                'title': menuroot.title,
                'link': menuroot.link,
                'published': menuroot.published,
                'on_click': menuroot.on_click,
                'expand': menu.expansion_depth >= menuroot.level,
                'selected': False,
                'leaf_selected': False,
                'children': [],
                'parent': None,
                'level': menuroot.level,
                'id': i + 1,
            }

            urls.append((menuroot.link, current_item))

        # Urls bust be sorted by key, otherwise the mark_selected and
        # make_breadcrumb won't work.
        urls.sort( key=itemgetter( 0 ), reverse=True )

        return {
            'tree': root,
            'byurls': urls,
        }

    except ObjectDoesNotExist:
        raise MenuDoesNotExist
    except IndexError:
        raise MenuDoesNotExist


def mark_selected_item( byurls, path ):
    """
    Highlighting of selected menu item

    Works like the bread crumb generation (see below).
    """

    path = get_language_from_path(path)[2]

    for url, val in byurls:
        if path.startswith( url ) and url != '':
            val['leaf_selected'] = True
            while val:
                if val['selected']:
                    break
                val['selected'] = True
                val = val['parent']
            return


def make_breadcrumb( byurls, path ):
    """
    Breadcrumb generation

    Takes a reverse-sorted list of URLs, and find the most specific
    URL for the requested path. E.g if the path is /a/b/c/ and the menu
    has two items /a/ and /a/b/ then /a/b/ will be chosen). Once the most
    specific item is chosen, it gets the corresponding menu item and
    follow it's parents to the root.

    It is imperative that the byurls is reverse-sorted for this
    breadcrumb generation to work as expected.
    """
    if path == '/':
        return []

    if settings.USE_I18N:
        lang = translation.get_language()

    for url, val in byurls:
        if settings.USE_I18N:
            url = get_path_for_language(lang, url)
        if path.startswith( url ) and url != '/' and url != '':
            crumb = []
            while val:
                if 'hide_menu_root' in val and val['hide_menu_root']:
                    break
                if settings.USE_I18N:
                    crumb.append( { 'title': val['title'], 'link': get_path_for_language(lang, val['link']), 'on_click': val['on_click'] } )
                else:
                    crumb.append( { 'title': val['title'], 'link': val['link'], 'on_click': val['on_click'] } )
                val = val['parent']
            crumb.reverse()
            return crumb

    return None


def get_menu( name ):
    """
    Retrieve the structure of a menu with a given name. The menu
    structure is cached, so the menu will only be generated if it's
    not in the cache. The cache is automatically invalidated, when a menu
    is updated.
    """
    key = CACHE_KEY + str(name.__hash__())
    menu = cache.get( key )
    if menu is None:
        menu = build_menu( name )
        cache.set( key, menu, settings.CACHE_MIDDLEWARE_SECONDS )

    return menu


def invalidate_menu_cache( sender, instance, signal, raw=False, *args, **kwargs ):
    """
    Invalidate the cache of a menu structure. Listens for updated/created/
    deleted Menu/MenuItem objects.
    """
    if not raw:
        menu_name = instance.name
        cache.delete( CACHE_KEY + str(menu_name.__hash__()) )


def invalidate_menu_item_cache( sender, instance, signal, raw=False, *args, **kwargs ):
    """
    Invalidate the cache of a menu structure. Listens for updated/created/
    deleted Menu/MenuItem objects.
    """
    if not raw:
        menu = instance.get_root().menu
        if menu:
            cache.delete( CACHE_KEY + str( menu.name.__hash__() ) )


def update_children_menu( sender, instance, signal, raw=False, *args, **kwargs ):
    '''
    If the 'menu' field has changed update the children accordingly.
    '''
    if not raw:
        try:
            obj = sender.objects.get(id=instance.id)
        except sender.DoesNotExist:
            # New MenuItem, nothing to do
            return

        if obj.menu != instance.menu:
            # Update descendants menus accordingly
            instance.get_descendants().update(menu=instance.menu)


def menu_cache_dependencies( sender, instance, signal, *args, **kwargs ):
    '''
    Method for cache invalidation of pages when menus are updated.
    TODO: We should probably invalidate all cache pages as they all show
    the full menu structure
    '''
    from djangoplicity.pages.models import Page, CACHE_KEY as PAGE_CACHE_KEY

    # Page caches need to be regenerated in case of menu changes
    qs = Page.objects.filter(embedded__exact=0)
    for p in qs:
        if not p.embedded:
            for url in p.url_set.all():
                cache.delete(PAGE_CACHE_KEY['pages'] + str(url.url.__hash__()))

# Listen for signals sent when Menu or MenuItems are updated/created/deleted
signals.post_save.connect(invalidate_menu_cache, sender=Menu)
signals.pre_delete.connect(invalidate_menu_cache, sender=Menu)
signals.post_save.connect(invalidate_menu_item_cache, sender=MenuItem)
signals.pre_save.connect(update_children_menu, sender=MenuItem)
signals.pre_delete.connect(invalidate_menu_item_cache, sender=MenuItem)

# Signals to invalide pages when menus are updated
signals.post_save.connect(menu_cache_dependencies, sender=Menu)
signals.post_save.connect(menu_cache_dependencies, sender=MenuItem)
signals.pre_delete.connect(menu_cache_dependencies, sender=Menu)
signals.pre_delete.connect(menu_cache_dependencies, sender=MenuItem)
