# -*- coding: utf-8 -*-
#
# djangoplicity
# Copyright (c) 2007-2011, European Southern Observatory (ESO)
# All rights reserved.
#
#

# See http://packages.python.org/distribute/setuptools.html#namespace-packages
try:
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError:
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)