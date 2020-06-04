# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

"""
Form Widget classes specific to the Djangoplicity admin site.
"""

from itertools import chain
from django import forms
from django.conf import settings
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils.html import escape, conditional_escape
from django.forms.utils import flatatt
from tinymce import TinyMCE

from djangoplicity.contrib.admin.templatetags import djangoplicity_admin_utils as djau


#
# Setup settings attributes in case they haven't been specified
#
class HierarchicalSelect( forms.Widget ):
    """
    A Widget for displaying ForeignKey for a django-mptt model so that the tree structure is
    apparent rather than a normal flat <selector> box.

    This is more or less a copy of django.newforms.widgets.Select
    """

    def __init__(self, attrs=None, choices=()):
        super(HierarchicalSelect, self).__init__(attrs)
        # choices can be any iterable, but we may need to render this widget
        # multiple times. Thus, collapse it into a list so it can be consumed
        # more than once.
        self.choices = list(choices)

    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = ''
        if attrs is None:
            attrs = {}
        final_attrs = self.build_attrs(attrs, {'name': name})
        output = [u'<select%s>' % forms.widgets.flatatt(final_attrs)]
        # Normalize to string.
        str_value = force_unicode(value)
        for obj in chain( self.choices.queryset, choices ):
            option_value = obj.pk
            option_value = force_unicode( option_value )

            if obj.level > 0:
                option_label = mark_safe( ( u'&nbsp;&nbsp;&nbsp;' * obj.level ) + u'&gt; ' + escape(obj.title) )
            else:
                option_label = mark_safe( escape(obj.title) )

            selected_html = (option_value == str_value) and u' selected="selected"' or ''
            output.append(u'<option value="%s"%s>%s</option>' % (
                    escape(option_value), selected_html,
                    conditional_escape(force_unicode(option_label))))
        output.append(u'</select>')
        return mark_safe(u'\n'.join(output))


class AdminRichTextAreaWidget(TinyMCE):
    def use_required_attribute(self, *args):
        return False



class RelationForeignKeyRawIdWidget(forms.TextInput):
    """
    A Widget for displaying ForeignKeys in the "raw_id" interface rather than
    in a <select> box, modified to work within the RelationEditor
    """
    def __init__(self, rel, attrs=None):
        self.rel = rel
        super(RelationForeignKeyRawIdWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        related_url = '../../../../../%s/%s/' % (self.rel.to._meta.app_label, self.rel.to._meta.object_name.lower())
        if self.rel.limit_choices_to:
            url = '?' + '&amp;'.join(['%s=%s' % (k, v) for k, v in self.rel.limit_choices_to.items()])
        else:
            url = ''
        if 'class' not in attrs:
            attrs['class'] = 'vForeignKeyRawIdAdminField'  # The JavaScript looks for this hook.
        output = [super(RelationForeignKeyRawIdWidget, self).render(name, value, attrs)]
        # TODO: "id_" is hard-coded here. This should instead use the correct
        # API to determine the ID dynamically.
        output.append('<a href="%s%s" class="related-lookup" id="lookup_id_%s" onclick="return showRelatedObjectLookupPopup(this);"> ' %
            (related_url, url, name))
        output.append('<img src="%s/admin/img/selector-search.gif" width="16" height="16" alt="Lookup"></a>' % settings.STATIC_URL)
        return mark_safe(u''.join(output))


class LinkWidget (forms.TextInput):
    def __init__(self, attrs=None):
        final_attrs = {'class': 'vTextField'}
        if attrs is not None:
            final_attrs.update(attrs)
        super(LinkWidget, self).__init__(attrs=final_attrs)

    def render(self, name, value, attrs=None):
        output = [super(LinkWidget, self).render(name, value, attrs)]
        output.append('<a href="%s" target="_blank"><span class="active selector-add" style="display: inline-block; margin-bottom: -5px; margin-left: 5px;"></span> </a>' %
            (value, ))
        return mark_safe(u''.join(output))


class BooleanIconDisplayWidget (forms.widgets.CheckboxInput):
    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        final_attrs = self.build_attrs(attrs, {'type': 'hidden', 'name': name})

        if value is True:
            final_val = 'on'
        elif value is False:
            final_val = 'off'
        else:
            final_val = ''

        final_attrs['value'] = final_val

        return mark_safe(u'<input%s />%s' % (flatatt(final_attrs), djau.display_boolean_icon(final_val)))


class StaticTextWidget (forms.widgets.TextInput):
    """ display text from a field, and use a hidden form to carry its data """
    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        final_attrs = self.build_attrs(attrs, {'type': 'hidden', 'name': name})

        final_attrs['value'] = value

        return mark_safe(u'<div style="font-weight:bold">%s<input%s /></div>' % (value, flatatt(final_attrs)))


class SelectorInput (forms.CheckboxInput):
    class Media:
        js = [
            'admin/js/core.js',
            'admin/js/vendor/jquery/jquery.js',
            'admin/js/jquery.init.js',
            'admin/js/admin/RelatedObjectLookups.js',
            'admin/js/actions.js',
            'admin/js/urlify.js',
            'admin/js/prepopulate.js',
            'admin/js/vendor/xregexp/xregexp.min.js',
        ]
