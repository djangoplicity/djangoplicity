# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from django import template
from django.template import Node

register = template.Library()


class ArchiveItemNode( Node ):
    def __init__( self, var, name, nodelist ):
        self.var = var
        self.name = name
        self.nodelist = nodelist

    def __repr__( self ):
        return "<ArchiveItemNode>"

    def render( self, context ):
        from djangoplicity.archives.contrib.satchmo.models import product_archive_item
        val = self.var.resolve( context )
        context.push()
        context[self.name] = product_archive_item( val )
        output = self.nodelist.render( context )
        context.pop()
        return output


@register.tag
def archiveitem( parser, token ):
    """
    Extracts the related archive item from a Satchmo product and
    adds it to the context (inside of this block) for caching and easy
    access.

    For example::
        {% load djangoplicity_satchmo %}
        {% archiveitem product as obj %}
            {{ obj.resource_thumb.url }}
        {% endarchiveitem %}
    """
    bits = list( token.split_contents() )

    if len( bits ) != 4 or bits[2] != "as":
        raise template.TemplateSyntaxError( "%r expected format is 'value as name'" % bits[0] )

    var = parser.compile_filter( bits[1] )
    name = bits[3]
    nodelist = parser.parse( ( 'endarchiveitem', ) )
    parser.delete_first_token()

    return ArchiveItemNode( var, name, nodelist )


@register.filter
def order_variable( value, arg ):
    """
    Extract the value of an custom order variable.
    """
    try:
        return value.get_variable( arg ).value
    except:
        return ""


@register.filter
def isocode2country( value ):
    """
    Replace ISO alpha-2 code with the country name.
    """
    from l10n.models import Country
    try:
        country = Country.objects.get( iso2_code=value )
        return country.name
    except:
        return ""


@register.filter
def isocode2printablecountry( value ):
    """
    Replace ISO alpha-2 code with the country name.
    """
    from l10n.models import Country
    try:
        country = Country.objects.get( iso2_code=value )
        return country.name
    except:
        return ""


@register.filter
def validatecontact( contact ):
    """
    Return true if the contact's email belong to ESO_DOMAINS
    """
    from djangoplicity.archives.contrib.satchmo.esoshipping.utils import validate_contact
    return validate_contact( contact)
