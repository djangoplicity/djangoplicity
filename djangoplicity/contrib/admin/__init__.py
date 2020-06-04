# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
from __future__ import unicode_literals

from functools import update_wrapper

from django.conf.urls import url
from django.contrib.admin.utils import unquote
from django.http import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from djangoplicity.contrib.admin.options import *
from djangoplicity.contrib.admin.widgets import *
from djangoplicity.utils.history import add_admin_history
from djangoplicity.utils.html_cleanup import clean_html


class CleanHTMLAdmin(object):
    '''
    Add option to clean HTML
    '''

    def get_urls( self ):
        # Tool to wrap class method into a view
        # START: Copied from django.contrib.admin.options
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name
        # END: Copied from django.contrib.admin.options

        urlpatterns = [
            url( r'^(.+)/cleanhtml/$',
                wrap( self.clean_html_view ),
                name='%s_%s_cleanhtml' % info ),
        ]

        # Note, must be last one, otherwise the change view
        # consumes everything else.
        urlpatterns += super(CleanHTMLAdmin, self).get_urls()

        return urlpatterns

    def _get_fields(self, obj, model):
        return [
            (field, getattr(obj, field), clean_html(getattr(obj, field)))
            for field in model.Archive.Meta.clean_html_fields
        ]


    def clean_html_view(self, request, object_id, extra_context=None):
        model = self.model
        opts = model._meta
        obj = self.get_object(request, unquote(object_id))

        if obj is None:
            raise Http404()

        fields = self._get_fields(obj, model)

        if request.method == 'POST':
            kwargs = dict([
                (name, after) for (name, _before, after) in fields
            ])

            model.objects.filter(pk=obj.pk).update(**kwargs)

            msg = 'HTML fields for {} {} were cleaned up'.format(
                opts.verbose_name, object_id)
            self.message_user(request, msg)

            add_admin_history(obj, 'Cleaned HTML fields', request.user)

            return redirect('{}:{}_{}_change'.format(
                self.admin_site.name, opts.app_label, opts.model_name),
                object_id)

        context = {
            'opts': opts,
            'obj': obj,
            'fields': fields,
        }

        return TemplateResponse(request, 'admin/cleanhtml_form.html', context)
