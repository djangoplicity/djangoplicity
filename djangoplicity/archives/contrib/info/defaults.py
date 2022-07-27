# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from builtins import str
from django.core.exceptions import ImproperlyConfigured
from functools import partial
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _, ugettext_noop
from djangoplicity.archives.contrib.queries.defaults import \
    CATEGORY_RELATION_FIELD, CATEGORY_URL_FIELD, CATEGORY_TITLE_FIELD
from django.conf import settings
from django.contrib.admin.utils import quote
from djangoplicity.utils.templatetags.djangoplicity_datetime import datetime as datetime_format
from datetime import time

__all__ = ('categories', 'admin_edit', 'admin_edit_for_site', 'admin_add_translation', 'published', 'featured', 'boolean_property', 'priority', 'release_date', 'paper_size', 'link_field')

import django
if django.VERSION >= (2, 0):
    from django.urls import NoReverseMatch, reverse
else:
    from django.core.urlresolvers import NoReverseMatch, reverse

# TODO Wed Jul 29 13:54:21 CEST 2015
# We use quote around the pk in reverse() to handle cases where the pk contains
# an underscore. This should be done automatically from Django 1.8 in which
# case the quote() calls can be removed, see:
# https://code.djangoproject.com/ticket/22266


def _categories(obj, relation_field=None, urlname_prefix=None, title_field=None, url_field=None, query_name=None):
    """
    Internal display helper for outputting categories for an archive object.

    See categories() instead.
    """
    try:
        categoryfield = getattr(obj, relation_field)

        # Fix for foreign key as well
        cats = categoryfield.all()

        html = ''
        for c in cats:
            if urlname_prefix:
                caturl = reverse("%s_query_%s" % (urlname_prefix, query_name), args=[getattr(c, url_field)])
                html += '<a href="%s">%s</a><br />' % (caturl, getattr(c, title_field))
            else:
                html += '%s<br />' % getattr(c, title_field)

        return mark_safe(html) or None
    except AttributeError:
        raise ImproperlyConfigured("Specified field names on category model does not exist.")


def categories(urlname_prefix=None, title=_('Categories'), url_field=CATEGORY_URL_FIELD, relation_field=CATEGORY_RELATION_FIELD, title_field=CATEGORY_TITLE_FIELD, query_name='category'):
    """
    Generic display helper for displaying categories for an archive object.

    Returns a specific display helper for a given category field.

    relation_field - the field name of the category model field (must be
                     a ForeignKey or ManyToManyField). Default: category
    title_field - the field name of category title value field in the
                     category model. Default: name
    url_field     - the field name of URL value field in the category model.
                     Default: url
    title         - Title of info field. Default: Categories.
    urlname_prefix - If specified then category names will be linked to the
                     archive query named by query_name (default: category).
                     The query must be a of type CategoryQuery. If not
                     specified, no links are made.
    query_name   - Query name for links to resolve to. Must be a CategoryQuery.

    Usage Example::
        class SomeArchiveOptions(ArchiveOptions):
            urlname_prefix = "images"

            info = (
                (_(u'Info'), { 'fields' : ('id', categories(urlname_prefix="images"))), }),
            )

            class Queries(object):
                category = CategoryQuery(...)
    """
    f = partial(_categories, relation_field=relation_field, urlname_prefix=urlname_prefix, title_field=title_field, url_field=url_field, query_name=query_name)
    f.short_description = title
    return f


def admin_edit(obj, admin_app='admin', proxy=None, translation_proxy=None):
    """
    Generic admin link helper for displaying an admin edit link.
    """
    try:
        # Determine module name to use.
        model_name = obj._meta.model_name

        if translation_proxy and obj.is_translation():
            model_name = translation_proxy._meta.model_name
        elif proxy:
            model_name = proxy._meta.model_name

        return reverse('%s:%s_%s_change' % (admin_app, obj._meta.app_label, model_name), args=[quote(obj.pk)])
    except NoReverseMatch:
        return None
admin_edit.short_description = ugettext_noop('Edit')


def admin_edit_for_site(site, proxy=None, translation_proxy=None):
    """
    Generic admin link helper for displaying an admin edit link for a
    custom admin instead of the default admin site.

    Note site name must be valid which means you need to specify it
    when creating the admin site. For instance:
    """
    f = partial(admin_edit, admin_app=site, proxy=proxy, translation_proxy=translation_proxy)
    f.short_description = admin_edit.short_description
    return f


def _admin_add_translation(obj, admin_app='admin', proxy=None, translation_proxy=None):
    """
    """
    if not translation_proxy or not settings.USE_I18N:
        return None
    try:
        return '%s?source=%s' % (reverse('%s:%s_%s_add' % (admin_app, obj._meta.app_label, translation_proxy._meta.model_name)), obj.pk)
    except NoReverseMatch:
        return None
_admin_add_translation.short_description = ugettext_noop('Add translation')


def admin_add_translation(site, proxy=None, translation_proxy=None):
    """
    Admin link helper for displaying an 'add translation' link
    """
    f = partial(_admin_add_translation, admin_app=site, proxy=proxy, translation_proxy=translation_proxy)
    f.short_description = _admin_add_translation.short_description
    return f


def boolean_property(prop):
    return mark_safe('<img src="%s/admin/img/icon-yes.svg" />' % settings.STATIC_URL if prop else '<img src="%s/admin/img/icon-no.svg" />' % settings.STATIC_URL)


def published(obj):
    return boolean_property(obj.published)
published.short_description = ugettext_noop("Published")


def featured(obj):
    return boolean_property(obj.featured)
featured.short_description = ugettext_noop("featured")


def priority(obj):
    return str(obj.priority) + " %"
priority.short_description = ugettext_noop("Priority")


def release_date(obj):
    if obj.release_date:
        if obj.release_date.time() == time(0, 0):
            return datetime_format(obj.release_date, arg='DATE')
        else:
            return datetime_format(obj.release_date, arg='DATETIME')
    else:
        return None
release_date.short_description = ugettext_noop("Release date")


def link_field(description, field):
    """
    Display helper for links.

    Usage::
        info = (
            (_(u'About the Image'), { 'links' : (link_field('Press Release','press_release_link'),) }),
        )
    """
    def f(obj):
        try:
            link = getattr(obj, field)
            return link
        except AttributeError:
            return None
    f.short_description = description

    return f


def paper_size(obj):
    """ Display helper - output the dimensions """
    try:
        if obj.width and obj.height:
            return '%s cm x %s cm' % (obj.width, obj.height)
        else:
            return None
    except AttributeError:
        return None
paper_size.short_description = ugettext_noop('Size')


def weight(obj):
    """ Display helper - output the dimensions """
    if obj.weight:
        return '%s g' % obj.weight
    else:
        return None
weight.short_description = ugettext_noop('Weight')
