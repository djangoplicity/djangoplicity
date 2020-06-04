# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from django.conf import settings


def get_archives():
    """
    Get a list of archive model, options.
    """
    return [( _do_import( model_string ), _do_import( option_string ) ) for ( model_string, option_string ) in settings.ARCHIVES]


def get_archive_modeloptions( app_label, module_name ):
    """
    Get the model and options for an archive using the app label and module name.
    """
    try:
        return get_archives_dict()[app_label][module_name]
    except KeyError:
        return None, None


def get_archives_dict():
    """
    Get a list of archive model, options.
    """
    models = {}
    for ( model_string, option_string ) in settings.ARCHIVES:
        model = _do_import( model_string )
        options = _do_import( option_string )

        app = model._meta.app_label
        mod = model._meta.model_name

        if app not in models:
            models[app] = {}

        models[app][mod] = ( model, options )

    return models


def _do_import( str ):
    """
    Import a an archive model defined by a string - e.g. "djangoplicity.media.models.Image".
    """
    ( name, _dot, cls ) = str.rpartition( '.' )
    mod = __import__( name )
    components = name.split( '.' )
    for comp in components[1:]:
        mod = getattr( mod, comp )
    return getattr( mod, cls )
