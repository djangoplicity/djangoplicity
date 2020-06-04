# -*- coding: utf-8 -*-
#
# djangoplicity-archives
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
from __future__ import unicode_literals

from collections import OrderedDict

from django import forms
from django.urls import reverse
from django.db.models import Q
from django.forms import fields as formsFields
from django.forms.forms import BoundField, conditional_escape, mark_safe
from django.http import Http404
from django.utils.encoding import force_unicode

# We don't want to use ugettext_lazy here as otherwise the advanced search
# parameters never get evaluated and are displayed as django.utils.functional.__proxy__
from django.utils.translation import ugettext as _


class AdvancedSearchForm( object ):
    """
    Encapsulates form and search methods for an Advanced Search
    """

    def __init__(self, options, request=None):
        self.options = options

        if request and request.GET:
            self.form = self._build_form(data=request.GET)
        else:
            self.form = self._build_form()

        self.repr()

    def url_list(self):
        urlname = "%s_query_search" % (self.options.urlname_prefix if self.options.urlname_prefix else None)

        return reverse(urlname)

    def search(self, queryset):
        """
        """
        if self.form.is_valid():
            qs = queryset.filter(self.query())
            return qs.distinct()
        else:
            return queryset.none()

    def query(self):
        q = Q()
        for key, f in self.form.fields.iteritems():
            q = q & f.query(value=self.form.cleaned_data[key])
        return q

    def repr(self):
        criteria = []

        header = ('%s' % self.options.urlname_prefix)

        for name, field in self.form.fields.items():
            bf = BoundField( self.form, field, name )

            repr = bf.field.repr( bf.data )
            if repr:
                repr = '%s %s' % ( _( bf.label ), repr )
                criteria.append( repr )

        if criteria:
            str = header + " with "
        else:
            return header + "."

        for c in criteria[:-1]:
            str += "%s, " % c

        for c in criteria[-1:]:
            str += c

        str += '.'

        return str

    def _build_form(self, data=None, options=None):
        class AdvancedSearchForm (forms.Form):
            _html_output = outputhelper

        if not options:
            options = self.options

        # take fields from options class, and sort them correctly
        fields = [(field_name, obj) for field_name, obj in options.AdvancedSearch.__dict__.iteritems() if isinstance(obj, formsFields.Field)]
        fields.sort(lambda x, y: cmp(x[1].creation_counter, y[1].creation_counter))

        for dummy_name, field in fields:
            if hasattr(field, 'choices'):
                # Dynamic fields such as AVMImageInstrumentSearchField have
                # their choices evaluated when accessed (through _get_choices),
                # and their widgets choices set when the Field choices are set
                # (through _set_choices) so we make sure this is done:
                field.choices = field.choices

        # inject them into ASF's base fields
        AdvancedSearchForm.base_fields = OrderedDict(AdvancedSearchForm.base_fields.items() + fields)

        return AdvancedSearchForm(data)


SEPARATOR_HTML = "<tr class='searchitemsepr'><td colspan='3'><h2>%(label)s</h2></td>"


def outputhelper(self, normal_row, error_row, row_ender, help_text_html, errors_on_separate_row, separator_html=SEPARATOR_HTML):
    "Helper function for outputting HTML. Used by as_table(), as_ul(), as_p()."
    top_errors = self.non_field_errors()  # Errors that should be displayed above all fields.
    output, hidden_fields = [], []

    for name, field in self.fields.items():
        html_class_attr = ''
        bf = BoundField(self, field, name)
        bf_errors = self.error_class([conditional_escape(error) for error in bf.errors])  # Escape and cache in local variable.

        # Check that we can get a unicode output of the field (in particular
        # if someone tries to pass bad data to the form
        try:
            unicode(bf)
        except TypeError:
            raise Http404

        if bf.is_hidden:
            if bf_errors:
                top_errors.extend([u'(Hidden field %s) %s' % (name, force_unicode(e)) for e in bf_errors])
            hidden_fields.append(unicode(bf))

        elif bf.field.is_separator():
            output.append(separator_html % {
                'label': conditional_escape(force_unicode(bf.label)),
            })

        else:
            # Create a 'class="..."' atribute if the row should have any
            # CSS classes applied.
            css_classes = bf.css_classes()
            if css_classes:
                html_class_attr = ' class="%s"' % css_classes

            if errors_on_separate_row and bf_errors:
                output.append(error_row % force_unicode(bf_errors))

            if bf.label:
                label = conditional_escape(force_unicode(bf.label))
                # Only add the suffix if the label does not end in
                # punctuation.
                if self.label_suffix:
                    if label[-1] not in ':?.!':
                        label += self.label_suffix
                label = bf.label_tag(label) or ''
            else:
                label = ''

            if field.help_text:
                help_text = help_text_html % force_unicode(field.help_text)
            else:
                help_text = u''

            output.append(normal_row % {
                'errors': force_unicode(bf_errors),
                'label': force_unicode(label),
                'field': unicode(bf),
                'help_text': help_text,
                'html_class_attr': html_class_attr
            })

    if top_errors:
        output.insert(0, error_row % force_unicode(top_errors))

    if hidden_fields:  # Insert any hidden fields in the last row.
        str_hidden = u''.join(hidden_fields)
        if output:
            last_row = output[-1]
            # Chop off the trailing row_ender (e.g. '</td></tr>') and
            # insert the hidden fields.
            if not last_row.endswith(row_ender):
                # This can happen in the as_p() case (and possibly others
                # that users write): if there are only top errors, we may
                # not be able to conscript the last row for our purposes,
                # so insert a new, empty row.
                last_row = (normal_row % {'errors': '', 'label': '',
                                            'field': '', 'help_text': '',
                                            'html_class_attr': html_class_attr})
                output.append(last_row)
            output[-1] = last_row[:-len(row_ender)] + str_hidden + row_ender
        else:
            # If there aren't any rows in the output, just append the
            # hidden fields.
            output.append(str_hidden)
    return mark_safe(u'\n'.join(output))
