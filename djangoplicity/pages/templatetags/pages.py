# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

from django import template
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from djangoplicity.pages.views import embed_page_key, PageNotFoundError, PageAuthorizationError
from djangoplicity.pages.models import PageGroup

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


class EmbeddedPageNode( template.Node ):
    """
    Embeds a page with the given page page key into a template.
    """
    def __init__(self, tokens, no_unpublished=False ):
        '''
        If no_unpublished is True unpublished pages will only be embedded if
        the 'preview' GET parameter is passed '''
        self.page_key = tokens[0]
        if len(tokens) > 1:
            self.page_key_variable = template.Variable(tokens[1])
        else:
            self.page_key_variable = None
        self.no_unpublished = no_unpublished

    def render(self, context):
        if not isinstance( context, template.RequestContext ):
            return node_error( _(u"Context must be of type RequestContext.") )
        try:
            key = self.page_key
            if self.page_key_variable:
                key += self.page_key_variable.resolve(context)
            return embed_page_key( context['request'], key, no_unpublished=self.no_unpublished )
        except PageNotFoundError as e:
            return node_error( _(u"The embedded page could not be found.") )
        except PageAuthorizationError as e:
            return node_error( _(u"User not authorized to view page.") )
        except template.VariableDoesNotExist as e:
            return node_error( _(u"Couldn't resolve request variable: %s") % e )

        return node_error( _(u"An unknown error occurred.") )


@register.tag( name="embed_page" )
def embed_page( parser, token ):
    """
    {% load pages %}
    {% embed_page page_key %}
    """
    tokens = token.split_contents()

    return EmbeddedPageNode( tokens[1:] )


@register.tag( name="embed_page_no_unpublished" )
def embed_page_no_unpublished( parser, token ):
    """
    {% load pages %}
    {% embed_page_no_unpublished page_key %}
    Similar to embed_page but won't embed unpublished pages unless
    the 'preview' GET parameter is passed

    """
    tokens = token.split_contents()

    if len(tokens) != 2:
        raise template.TemplateSyntaxError(_( u"embed_page tag requires one argument" ))

    return EmbeddedPageNode( tokens[1:], no_unpublished=True )


@register.simple_tag( name='user_can_edit' )
def user_can_edit(user, page):
    """
    {% load pages %}
    {% user_can_edit user page %}
    Returns True if the current user can edit the page
    """
    if user.is_anonymous:
        return False

    # If we don't have any configured PageGroup we assume
    # standard permissions apply:
    if PageGroup.objects.count() == 0:
        return True

    # Get list of Page Groups the user belong to
    pgroups = PageGroup.objects.filter(groups__in=user.groups.all())

    full_access = any([ x.full_access for x in pgroups ])

    if user.is_superuser or full_access:
        return True

    for group in page.groups.all():
        if group in pgroups:
            return True

    if settings.USE_I18N and page.is_translation():
        # For translated pages access is given if one has access
        # to the PageProxy, or if one belongs to any page group
        # of the source page
        for group in page.source.groups.all():
            if group in pgroups:
                return True

        if user.has_perm('pages.change_pageproxy'):
            return True

    return False
