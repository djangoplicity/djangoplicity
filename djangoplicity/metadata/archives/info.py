# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from builtins import str
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_noop as _

__all__ = ( 'subject_name', 'subject_category', 'facility', 'instruments' )


def subject_name( obj ):
    """
    Display helper for showing the Subject.Name attribute.
    """
    subject_names = obj.subject_name.all()
    link = '<a href="%s">%s</a>'

    names = []
    for sn in subject_names:
        if sn.simbad_link():
            names.append( link % ( sn.simbad_link(), str( sn ) ) )
        elif sn.wiki_link:
            names.append( link % ( sn.wiki_link, str( sn ) ) )
        else:
            names.append(str(sn))

    return mark_safe(", ".join(names))


subject_name.short_description = _("Name")


def _simbad_link(obj):
    return [ sn.simbad_link for sn in obj.subject_name.all() ]


subject_name.simbad_link = _simbad_link


def facility( obj ):
    """
    Display helper for showing the Subject.Name attribute.
    """
    facilities = []
    for f in obj.facility.all():
        if f.wiki_link:
            facilities.append('<a href="%s">%s</a>' % (f.wiki_link, str(f)))
        else:
            facilities.append(str(f))

    return mark_safe(', '.join(facilities))


facility.short_description = _("Facility")


def instruments( obj ):
    """
    Display helper for showing the Subject.Name attribute.
    """
    result = []
    for i in obj.instruments.all():
        if i.wiki_link:
            result.append('<a href="%s">%s</a>' % (i.wiki_link, str(i)))
        else:
            result.append(str(i))

    return mark_safe(', '.join(result))


instruments.short_description = _("Instruments")


def subject_category( obj ):
    """
    Display helper for showing the Subject.Name attribute.
    """
    cat = "<br />".join( ["%s" % str(x) for x in obj.subject_category.all()] )

    if cat:
        return mark_safe( cat )
    else:
        return ''


subject_category.short_description = _("Type")
