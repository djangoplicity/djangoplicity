# -*- coding: utf-8 -*-
#
# djangoplicity-archives
# Copyright (c) 2007-2011, European Southern Observatory (ESO)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the European Southern Observatory nor the names
#      of its contributors may be used to endorse or promote products derived
#      from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY ESO ``AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL ESO BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE

"""
Run tests as::

    python ../djangoplicity/src/djangoplicity/archives/contrib/search/tests.py
"""

from djangoplicity.archives.contrib.search.queryparser import QueryParser, \
    AstronomyQueryParser
import unittest


class QueryParserTestCase( unittest.TestCase ):
    def assert_criterion(self, criterion, sign, kw, phrase ):
        self.assertEqual(criterion.sign, sign)
        self.assertEqual(criterion.keyword, kw)
        self.assertEqual(criterion.is_phrase, phrase)

    def assert_criteria(self, criteria, expected ):
        for c in criteria:
            e = expected.pop(0)
            self.assert_criterion( c, *e )

        self.assertEqual(len(expected), 0)

    def test_parser(self):
        self.assert_criteria( QueryParser.parse("term1"), [('', 'term1', False), ] )
        self.assert_criteria( QueryParser.parse("term1 term2"), [('', 'term1', False), ('', 'term2', False)] )
        self.assert_criteria( QueryParser.parse("   term1    term2    "), [('', 'term1', False), ('', 'term2', False)] )
        self.assert_criteria( QueryParser.parse("+term1 -term2"), [('+', 'term1', False), ('-', 'term2', False)] )
        self.assert_criteria( QueryParser.parse('" this is a phrase "'), [('', ' this is a phrase ', True), ] )
        self.assert_criteria( QueryParser.parse('" this is a phrase " "also a phrase"'), [('', ' this is a phrase ', True), ('', 'also a phrase', True)] )
        self.assert_criteria( QueryParser.parse('-" this is a phrase " +"also a phrase"'), [('-', ' this is a phrase ', True), ('+', 'also a phrase', True)] )
        self.assert_criteria( QueryParser.parse('-"mixed phrase" +term'), [('-', 'mixed phrase', True), ('+', 'term', False)] )
        self.assert_criteria( QueryParser.parse('-wild_$5^#-chars'), [('-', 'wild_$5^#-chars', False), ] )

    def test_quey_expansion(self):
        self.assert_criteria( AstronomyQueryParser.parse("term1"), [('', 'term1', False), ] )

        # Widening of query
        # Base cases:
        self.assert_criteria( AstronomyQueryParser.parse("M51"), [('', 'M51', False), ('', 'M 51', True), ] )
        self.assert_criteria( AstronomyQueryParser.parse('"M 51"'), [('', 'M 51', True), ('', 'M51', False)] )

        # Additional cases:
        self.assert_criteria( AstronomyQueryParser.parse('" M 51 "'), [('', 'M 51', True), ('', 'M51', False)] )
        self.assert_criteria( AstronomyQueryParser.parse("-M51"), [('-', 'M51', False), ] )
        self.assert_criteria( AstronomyQueryParser.parse("+M51"), [('', 'M51', False), ('', 'M 51', True), ] )

        # Narrowing of query
        self.assert_criteria( AstronomyQueryParser.parse("M 51"), [('', 'M51', False), ('', 'M 51', True), ] )


if __name__ == '__main__':
    unittest.main()
