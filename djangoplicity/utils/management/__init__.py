# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
import os
import sys
import imp


def find_management_module_replacement(app_name):
    """
    Determines the path to the management module for the given app_name,
    without actually importing the application or the management module.

    Raises ImportError if the management module cannot be found for any reason.

    See http://code.djangoproject.com/ticket/14087
    """
    parts = app_name.split('.')
    parts.append('management')
    parts.reverse()
    part = parts.pop()
    paths = None

    # When using manage.py, the project module is added to the path,
    # loaded, then removed from the path. This means that
    # testproject.testapp.models can be loaded in future, even if
    # testproject isn't in the path. When looking for the management
    # module, we need look for the case where the project name is part
    # of the app_name but the project directory itself isn't on the path.
    try:
        modules = find_modules(part, paths)
        paths = [m[1] for m in modules]
    except ImportError, e:
        # When namespace packages are installed with python setup.py install --single-version-externally-managed
        # will not have a __init__.py file in the directory. Instead there'll be a .pth file in site-packges
        # with a bit of python code that will add the namespace package as builtin module and set it's path (i.e it's
        # added to sys.modules). Thus, in case the find_module cannot locate the module, we'll have a look if it's
        # already loaded in sys.modules.
        # TODO: This only takes care of the problem where the namespace package is a toplevel package - e.g djangoplicity
        # but not djangoplicity.nsapp
        if part in sys.modules:
            paths = sys.modules[part].__path__
        elif os.path.basename(os.getcwd()) != part:
            raise e

    while parts:
        part = parts.pop()
        modules = find_modules(part, paths)
        paths = [m[1] for m in modules]

    return paths[0]


def find_modules(name, path=None):
    """Find all modules with name 'name'

    Unlike find_module in the imp package this returns a list of all
    matched modules.

    See http://code.djangoproject.com/ticket/14087
    """
    results = []
    if path is None:
        path = sys.path
    for p in path:
        importer = sys.path_importer_cache.get(p, None)
        if importer is None:
            find_module = imp.find_module
        else:
            find_module = importer.find_module

        try:
            result = find_module(name, [p])
            if result is not None:
                results.append(result)
        except ImportError:
            pass
    if not results:
        raise ImportError("No module named %.200s" % name)
    return results


def fix_find_management_module():
    """
    The django management module cannot find management commands in namespace packages.
    This hack replaces the django find_management_module funciton with one that support
    namespace packages. It's based on ticket http://code.djangoproject.com/ticket/14087
    which is ready for checkin for Django 1.3, but not sure to make it yet.

    To use it edit your projects manage.py and add change the following::

        if __name__ == "__main__":
            execute_manager(settings)

    into::

        if __name__ == "__main__":
            from djangoplicity.utils.management import fix_find_management_module
            fix_find_management_module()
            execute_manager(settings)
    """
    from django.core import management
    func = management.find_management_module
    find_management_module_replacement.__doc__ = func.__doc__
    find_management_module_replacement.__name__ = func.__name__
    management.find_management_module = find_management_module_replacement
