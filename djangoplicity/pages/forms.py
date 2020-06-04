# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

from django import forms
from django_ace import AceWidget

from djangoplicity.contrib.admin.widgets import AdminRichTextAreaWidget
from djangoplicity.pages.models import Page


class PageForm(forms.ModelForm):
    '''
    We use a custom Form to use the AceWidget if the page is in "raw html" mode
    '''
    script = forms.CharField(widget=AceWidget(mode='javascript', width='100%'), required=False)
    content = forms.CharField(widget=AdminRichTextAreaWidget({'height': '800'}))

    def __init__(self, *args, **kwargs):
        super(PageForm, self).__init__(*args, **kwargs)

        try:
            instance = kwargs['instance']
            if instance.raw_html:
                self.fields['content'].widget = AceWidget(mode='html', width='100%', height='500px')
        except (KeyError, AttributeError):
            pass

    class Meta:
        model = Page
        fields = '__all__'
