# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from djangoplicity.archives.urls import urlpatterns_for_options
from djangoplicity.products2.options import *


urlpatterns = urlpatterns_for_options( STECFNewsletterOptions )
