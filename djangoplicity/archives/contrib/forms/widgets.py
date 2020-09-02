# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

from django.conf import settings
from django.forms.utils import flatatt
from django import forms
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

__all__ = ( 'PriorityWidget', )


class PriorityWidget( forms.HiddenInput ):
    class Media:
        css = {
            'all': (settings.JQUERY_UI_CSS, settings.DJANGOPLICITY_ADMIN_CSS)
        }
        js = (
            settings.JQUERY_JS,
            settings.JQUERY_UI_JS,
            settings.DJANGOPLICITY_ADMIN_JS,
        )

    def __init__(self, attrs=None, slider_attrs=None, slider_val_attrs=None):
        if attrs is None:
            attrs = {}
        if slider_attrs is None:
            slider_attrs = {'class': 'vPrioritySlider'}
        if slider_val_attrs is None:
            slider_val_attrs = {'class': 'vPrioritySliderVal'}

        self.slider_attrs = slider_attrs
        self.slider_val_attrs = slider_val_attrs
        super(PriorityWidget, self).__init__(attrs=attrs)

    @property
    def is_hidden(self):
        return False

    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        final_attrs = self.build_attrs(attrs,
            {'type': self.input_type, 'name': name})
        slider_attrs = self.build_attrs(self.slider_attrs,
            {'id': '_'.join(['id', name, 'slider'])})
        slider_val_attrs = self.build_attrs(self.slider_val_attrs,
            {'id': '_'.join(['id', name, 'slider_val'])})

        if value is None:
            value = ''
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_text(value)

        attrs = {
            'slider_attrs': flatatt(slider_attrs),
            'slider_val_attrs': flatatt(slider_val_attrs),
            'final_attrs': flatatt(final_attrs),
            'slider_container': flatatt({'class': 'vPrioritySliderContainer'}),
        }

        return mark_safe(u'<div%(slider_container)s><div%(slider_attrs)s></div><div%(slider_val_attrs)s></div></div><input%(final_attrs)s/><br/>' % attrs )
