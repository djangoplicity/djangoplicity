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

from django import template
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from djangoplicity.menus.models import mark_selected_item, MenuDoesNotExist, MenuProxy, make_breadcrumb

MENU_TMPL_NAME = u'menus/menu.html'

register = template.Library()


def node_error( e ):
    """
    Helper function to output an error message when
    rendering a template tag.
    """
    if settings.DEBUG:
        return u'[%s]' % e
    else:
        return u''  # Fail silently if DEBUG is not on.


class MenuNode( template.Node ):
    """
    Node for taking care of rendering a menu. See documentation for {% render_menu %}
    tag for more information.
    """

    def __init__( self, menu_var_name, template_name ):
        self.menu_var_name = menu_var_name

        if template_name is None:
            template_name = u'default'
        self.template_name = template_name

    def render( self, context ):
        """
        Note: django.core.context_processors.request must be added to the
        list of context processors.
        """
        # Load menu
        try:
            menu_proxy = template.Variable( self.menu_var_name ).resolve( context )
            menu = menu_proxy.get_menu()

            if 'request' in context:
                mark_selected_item( menu['byurls'], context['request'].path )

        except MenuDoesNotExist as e:
            return node_error( u"The menu '%s' does not exists" % menu_proxy.menu_name )
        except template.VariableDoesNotExist as e:
            return node_error( _(u"Couldn't resolve menu variable: %s") % e )

        # Render template and report any errors if debug is on
        try:
            t = template.loader.get_template( MENU_TMPL_NAME )
        except template.TemplateDoesNotExist as e:
            return node_error( u"The template %s does not exists: %s" % (MENU_TMPL_NAME, e) )
        except template.TemplateSyntaxError as e:
            return node_error( u"The template %s had syntax errors: %s" % (MENU_TMPL_NAME, e) )

        return t.render({
            'hide_root': menu['tree']['hide_menu_root'],
            'root': menu['tree'],
            'template': self.template_name,
        })


class SubMenuNode( template.Node ):
    """
    Node for taking care of rendering a submenu. See documentation for {% render_submenu %}
    tag for more information.
    """

    def __init__( self, submenu_var, template_name ):
        self.submenu_var = submenu_var
        self.template_name = template_name

    def render( self, context ):
        try:
            submenu = template.Variable( self.submenu_var ).resolve( context )
        except template.VariableDoesNotExist as e:
            return node_error( u"Couldn't resolve variable in submenu: %s" % e )

        ctx = {}
        ctx['submenu'] = submenu

        # TODO: Remove true condition, once old code has been updated (LHN 12 Nov 2008).
        # Change from: {% render_submenu entry.children template %}
        # Change to: {% render_submenu entry.children %}
        if self.template_name is not None and self.template_name == "template":
            try:
                ctx['template'] = template.Variable( "template" ).resolve( context )
            except template.VariableDoesNotExist as e:
                return node_error( u"Couldn't resolve variable in submenu: %s" % e )
        else:
            if self.template_name is None:
                try:
                    ctx['template'] = template.Variable( "template" ).resolve( context )
                except template.VariableDoesNotExist as e:
                    return node_error( u"Couldn't resolve variable in submenu: %s" % e )
            else:
                ctx['template'] = self.template_name

        # Render template and report any errors if debug is on
        try:
            tplname = u'menus/submenu_%s.html' % ctx['template']
            t = template.loader.get_template( tplname )
        except template.TemplateDoesNotExist as e:
            return node_error( u"The template %s does not exists: %s" % ( tplname, e) )
        except template.TemplateSyntaxError as e:
            return node_error( u"The template %s had syntax errors: %s" % (tplname, e) )

        return t.render( ctx )


class InitMenuNode( template.Node ):
    """
    Stores a MenuProxy object in the current context with a user defined
    variable name. Request for menus is proxied through an object, to make
    sure the menu is not put in the context, unless it's really needed.
    """
    def __init__(self, menu_name, var_name):
        if menu_name[0] == menu_name[-1] and menu_name[0] in ('"', "'"):
            self.menu_name = menu_name[1:-1]
            self.menu_name_var = None
        else:
            self.menu_name_var = template.Variable(menu_name)

        self.var_name = var_name

    def render(self, context):
        if self.menu_name_var:
            self.menu_name = self.menu_name_var.resolve(context)
        context[self.var_name] = MenuProxy(self.menu_name)
        return ''


class BreadcrumbNode( template.Node ):
    """
    Stores a MenuProxy object in the current context with a user defined
    variable name. Request for menus is proxied through an object, to make
    sure the menu is not put in the context, unless it's really needed.
    """
    def __init__(self, var_names ):
        self.var_names = var_names

    def render(self, context):

        try:
            menu_proxies = [ template.Variable( name ).resolve( context ) for name in self.var_names ]

            for proxy in menu_proxies:
                menu = proxy.get_menu()
                crumb = make_breadcrumb( menu['byurls'], context['request'].path )
                if crumb is not None:
                    break

            if crumb is not None:
                # Render template and report any errors if debug is on
                t = template.loader.get_template( u'menus/breadcrumb.html' )
                return t.render({'breadcrumb': crumb})
            else:
                return ''

        except MenuDoesNotExist as e:
            return node_error( _(u"The menu does not exists") )
        except template.VariableDoesNotExist as e:
            return node_error( _(u"Couldn't resolve menu variable: %s") % e )
        except template.TemplateDoesNotExist as e:
            return node_error( _(u"The template %(tpl)s does not exists: %(msg)s") % { 'tpl': MENU_TMPL_NAME, 'msg': e } )
        except template.TemplateSyntaxError as e:
            return node_error( _(u"The template %(tpl)s had syntax errors: %(msg)s") % { 'tpl': MENU_TMPL_NAME, 'msg': e } )

        return node_error( _(u"An unknown error occurred.") )


@register.tag( name="render_menu" )
def render_menu( parser, token ):
    """
    Render a menu using a given template. If no template is specified,
    then the default template will be used.

    Usage::
        {% load menus %}
        {% init_menu '[menu_name]' as [var_name] %}
        {% render_menu [var_name] %}

    or::

        {% render_menu [var_name] [template_name] %}

    [var_name]    - Variable holding a MenuProxy object (created with the init_menu tag). A menu name is unique.
    [template_name] - (Optional) The template to use for rendering the menu.
                        The actual name will be menus/submenu_<template_name>.html

    Uses a template named menus/menu.html, which delegates the actually rendering
    of the menu tree to the {{ render_submenu }} template tag. The following
    variables can be used in the menu.html template::
        {{ hide_root }}
        {{ template }}
        {{ root }}
        {{ root.title }}
        {{ root.link }}
        {{ root.published }}
        {{ root.on_click }}
        {{ root.expand }}
        {{ root.selected }}
        {{ root.leaf_selected }}
        {{ root.children }}
        {{ root.parent }} (is always None)
        {{ root.level }} (is always 0)

    The following variables can be used in the menus/submenu_<template_name>.html
    template:
        {{ template }}
        {{ submenu }}
        {{ submenu[i].title }}
        {{ submenu[i].link }}
        {{ submenu[i].published }}
        {{ submenu[i].level }}
        {{ submenu[i].on_click }}
        {{ submenu[i].selected }}
        {{ submenu[i].leaf_selected }}
        {{ submenu[i].expand }}
        {{ submenu[i].children }}

    See MenuNode.render(...) for more info of the variables.
    """
    tokens = token.split_contents()

    if len( tokens ) < 2 or len( tokens ) > 3:
        raise template.TemplateSyntaxError( _(u"'%r' tag requires 1 or 2 arguments.") % tokens[0] )

    var_name = tokens[1]

    # Determine if template_name was provided, and if it exists.
    if len( tokens ) == 3:
        template_name = tokens[2]
    else:
        template_name = None

    return MenuNode( var_name, template_name )


@register.tag( name="render_submenu" )
def render_submenu( parser, token ):
    """
    Render the children of a menu item. This is normally not called directly
    but is called implicitly through {% render_menu %}-tag. You may however
    want to change or add templates used by this tag. See documentation for
    {% render_menu %} for more information.

    Usage::
        {% load menus %}
        {% render_submenu [children] [template_name] %}

    [children]    - A list of menu items
    [template_name] - (Optional) The template to use for rendering the menu.
                        The actual name will be menus/submenu_<template_name>.html.

                        Deprecation notice  (12 Nov 2008):
                        Old description was - (Required) the name of the *variable*
                        holding the template name.

                        For transition, if the template_name is "template" (which was
                        the default and only supported behavior previously) the tag
                        will work the old way. The feature will be removed once
                        all old code have been updated.

                        Please update::
                            {% render_submenu entry.children template %}
                        to::
                            {% render_submenu entry.children %}


    """
    tokens = token.split_contents()

    if len( tokens ) < 2 or len( tokens ) > 3:
        raise template.TemplateSyntaxError( _(u"'%r' tag requires 1 or 2 arguments.") % tokens[0] )

    submenu_var = tokens[1]

    # Determine if template_name was provided, and if it exists.
    if len( tokens ) == 3:
        template_name = tokens[2]
    else:
        template_name = None

    return SubMenuNode( submenu_var, template_name )


@register.tag
def init_menu( parser, token ):
    """
    {% load menus %}
    {% init_menu 'Main menu' as main_menu %}

    {% render_menu main_menu %}
    {% breadcrumb main_menu %}
    """
    try:
        tag_name, menu_name, fixed_as, var_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(_(u"%r tag requires arguments") % token.contents.split()[0])

    if fixed_as != 'as':
        raise template.TemplateSyntaxError(_(u"%r tag had invalid arguments") % tag_name)

    return InitMenuNode(menu_name, var_name)


@register.tag
def breadcrumb( parser, token ):
    """
    {% load menus %}
    {% init_menu 'Main menu' as main_menu %}
    {% breadcrumb main_menu ... %}
    """
    tokens = token.split_contents()

    if len(tokens) < 2:
        raise template.TemplateSyntaxError(( u"%r tag requires at least one argument" ) % tokens[0])

    return BreadcrumbNode( tokens[1:] )


@register.inclusion_tag('menus/breadcrumb_append.html')
def breadcrumb_append( title, link=None ):
    """
    {% load menus %}
    {% breadcrumb_append link title %}
    """
    return {
        'link': link,
        'title': title,
    }


class ResetCounterNode( template.Node ):
    """
    """
    def __init__( self, variable_name ):
        self.variable_name = variable_name

    def render( self, context ):
        context[self.variable_name] = 0
        return ''


class CounterNode( template.Node ):
    """
    """
    def __init__( self, variable_name ):
        self.variable_name = variable_name

    def render( self, context ):
        try:
            count = template.Variable( self.variable_name ).resolve( context )
        except template.VariableDoesNotExist:
            count = 0

        context[self.variable_name] = count + 1
        return context[self.variable_name]


@register.tag
def reset_counter( parser, token ):
    """
    """
    try:
        tag_name, var_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(u"%r tag requires one argument" % tag_name)

    return ResetCounterNode( var_name )


@register.tag
def counter( parser, token ):
    """
    """
    try:
        tag_name, var_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(u"%r tag requires one argument" % tag_name)

    return CounterNode( var_name )
