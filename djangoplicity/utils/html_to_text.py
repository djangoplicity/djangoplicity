# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#


"""
Wrapper around html2text package so we can extend some of its functionality,
namely by adding baseurls to inline links
"""

from html2text import HTML2Text
try:
    import urlparse
except ImportError:  # Python3
    import urllib.parse as urlparse


class DjangoplicityHTML2Text(HTML2Text):

    def handle_tag(self, tag, attrs, start):

        self.body_width = 0

        if attrs is None:
            attrs = {}
        else:
            attrs = dict(attrs)

        if tag == "a" and not self.ignore_links:
            if start:
                if 'href' in attrs and not (self.skip_internal_links and attrs['href'].startswith('#')):
                    self.astack.append(attrs)
                    self.o("[")
                else:
                    self.astack.append(None)
            else:
                if self.astack:
                    a = self.astack.pop()
                    if a:
                        if self.inline_links:
                            self.o("] - " + urlparse.urljoin(self.baseurl, a['href']) + " ")
                        else:
                            i = self.previousIndex(a)
                            if i is not None:
                                a = self.a[i]
                            else:
                                self.acount += 1
                                a['count'] = self.acount
                                a['outcount'] = self.outcount
                                self.a.append(a)
                            self.o("][" + str(a['count']) + "]")

        else:
            # old style class inheritance
            return HTML2Text.handle_tag(self, tag, attrs, start)
