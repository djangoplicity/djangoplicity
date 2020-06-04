# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

FUNC_NAME = 'register_with_admin'


def autoregister( admin_site, module ):
    """
    Looks for a method with name FUNC_NAME
    in the given module. If it exist, it will
    call the function with the given admin site
    as parameter.
    """
    if hasattr( module, FUNC_NAME ):
        func = getattr(module, FUNC_NAME)

        try:
            func( admin_site )
            return True
        except TypeError:
            return False
