# -*- coding: utf-8 -*-
#
# Djangoplicity
# Copyright 2007-2010 ESO & ESA/Hubble
#
# $Id$

"""
:mod:`testcases` -- Djangoplicity TestCases
===========================================

.. module:: testcases
   :synopsis: Additional test cases to supplement Django test cases.
.. moduleauthor:: Lars Holm Nielsen <lnielsen@eso.org>
"""
import unittest
import urllib2
from django.test import TestCase


class AdminTestCase( TestCase ):
    """
    :deprecated:
    """
    fixtures = ['auth.json' ]

    def setUp(self):
        self.failUnless( self.client.login( username='test', password='test' ) )


class RedirectTestCase( unittest.TestCase ):
    """
    Test case

    Example::
        class WebsiteRedirectsTestCase( RedirectTestCase ):
            def test_redirects(self):
                base = 'http://w4'
                links = [
                    ('/public/outreach/products/publ/calendars/','/public/outreach/products/calendarss/'),
                    ('/public/outreach/products/publ/ann-report/','/public/outreach/products/ann-report/'),
                ]
                self.assertRedirects( base, links )
    """

    def assertRedirect( self, old, new ):
        """ Assert that `old` URL is redirected to `new` URL. """
        u = urllib2.urlopen( old )
        self.assertEqual( u.geturl(), new )

    def assertRedirects(self, base, links ):
        """
        Test that all links defined in `self.links` are redirected. The test fails if one
        or more of the links fails.
        """
        failures = []
        httperrors = []

        for l in links:
            old = base + l[0] if base else l[0]
            new = base + l[1] if base else l[1]
            try:
                self.assertRedirect( old, new )
            except AssertionError:
                failures.append( old )
            except urllib2.HTTPError, e:
                httperrors.append( (str(e), old) )

        if httperrors:
            raise AssertionError( "Following links caused an HTTP error: %s" % httperrors )
        if failures:
            raise AssertionError( "Following links where not correctly redirected: %s" % failures )
