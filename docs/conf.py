# -*- coding: utf-8 -*-
#
# IAU Website & Membership Database
# Copyright 2007-2008 ESA/Hubble & International Astronomical Union
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#   Hosam Hassan <hhassan@eso.org>
#

import sys, os, datetime

from djangoplicity.sphinxconf import *

# General substitutions.
project = 'djangoplicity'
copyright = '2007-%s European Space Agency & European Southern Observatory' % current_year 

# The default replacements for |version| and |release|, also used in various
# other places throughout the built documents.
#
# The short X.Y version.
version = read_version()
# The full version, including alpha/beta/rc tags.
release = version

# Output file base name for HTML help builder.
htmlhelp_basename = 'djangoplicitydoc'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, document class [howto/manual]).
latex_documents = [
  ('index', 'djangoplicity.tex', 'Djangoplicity Documentation', 'European Space Agency \& European Southern Observatory', 'manual'),
]
