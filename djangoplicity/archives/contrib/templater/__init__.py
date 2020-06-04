# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template, loader
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.sites.models import Site


class DisplayTemplate (object):

    creation_counter = 0

    def __init__(self, typ, template, name='', embargo=False):
        self.creation_counter = DisplayTemplate.creation_counter
        DisplayTemplate.creation_counter += 1
        self.type = typ
        self.template = template
        self.name = name
        self.embargo = embargo

    def get(self):
        return (self.type, self.template)


class DEFAULT_SETTINGS (object):
    """
    settings are as follows:

    display_mode = (type, tmpl)

    Where type can either be 'template' (ie template = django.template.Template(tmpl)
    This is useful for quick templating like '{{obj}}'
    or 'file', where template will be django.template.loader.get_template(tmpl)
    for more advanced templates.

    """
    default = DisplayTemplate('template', '{{obj}}')


class Templater (object):
    """
    Display helper class. Allows you to specify different display modes for archive
    objects in their Options class.
    Helpful for rendering "views" on different templates, such as CSV, Email, etc.
    """

    def __init__(self, obj, options):

        self.settings = options.Display if hasattr(options, 'Display') else DEFAULT_SETTINGS
        self.obj = obj
        self.model = obj.__class__
        self.options = options

    def render(self, display='default', context=None):
        if context is None:
            context = {}

        display_type = self.settings.__dict__.get(display)

        typ, tmpl = display_type.get()

        context['obj'] = self.obj
        # gets the extra context from the ArchiveOptions
        context['extra_context'] = self.options.extra_context(self.obj)
        context['embargo_login'] = settings.ARCHIVE_EMBARGO_LOGIN
        context['embargo'] = display_type.embargo
        context['site_url_prefix'] = "http://" + Site.objects.get_current().domain

        if typ == 'template':
            template = Template(tmpl)
            return template.render(Context(context))
        elif typ == 'file':
            return render_to_string(tmpl, context)
        else:
            raise ImproperlyConfigured("Unrecognized template type. Valid types are 'file' or 'template'")
