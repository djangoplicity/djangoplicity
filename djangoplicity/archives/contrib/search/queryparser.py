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
Astronomy-aware query parser.
"""

from future import standard_library
standard_library.install_aliases()
from builtins import chr
from builtins import object
import re
from html.entities import codepoint2name
from django.utils.encoding import python_2_unicode_compatible

__all__ = ['QueryParser', 'AstronomyQueryParser']

unichr2entity = dict((chr(code), u'&%s;' % name) for code, name in codepoint2name.items() if code != 38)  # exclude "&"


@python_2_unicode_compatible
class Criterion( object ):
    PLUS = '+'
    MINUS = '-'
    NO_SIGN = ''

    def __init__(self, keyword, sign=PLUS, is_phrase=False ):
        self.sign = sign
        self.keyword = keyword
        self.is_phrase = is_phrase

    def is_mandatory(self):
        """ Determines if the query is a mandatory query. """
        return self.sign == self.PLUS or self.sign == self.MINUS

    def is_include(self):
        return self.sign == self.PLUS

    def is_exclude(self):
        return self.sign == self.MINUS

    def __repr__(self):
        if self.is_phrase:
            return '%s%s' % ( self.sign, self.keyword )
        else:
            return '%s"%s"' % ( self.sign, self.keyword )

    def __str__(self):
        return self.__repr__()


class QueryParser( object ):
    r"""
    Implements a simplistic parser for the following query grammar
    (EBNF-notation extended with some regular expressions)

    <query>    ::= <criterion>*
    <criterion> ::= <sign> <keyword>
    <sign>     ::= <empty string> | + | -
    <keyword>  ::= "<phrase>"
            |   <term>
    <phrase>   ::= [^"]*?
    <term>     ::= [^\s]+
    """
    SIGN_PATTERN = re.compile(r"^(\+|-)\s*")
    PHRASE_PATTERN = re.compile(r"""^(")([^"]*?)"\s*""")
    TERM_PATTERN = re.compile(r"^([^\s]+)\s*")

    @classmethod
    def parse( cls, searchstr, match_all=False, exact_match=False ):
        """
        Parse a search query into a list of criteria.

        A search query can have mandatory criteria and non-mandatory criteria. An
        list of criteria is fulfilled if:
        - all mandatory criteria are fulfilled, or
        - the query doesn't have any mandatory criteria, and at least one
            non-mandatory criteria is fulfilled.
        """
        searchstr = searchstr.strip()
        criteria = []

        if exact_match:
            criteria.append( Criterion( searchstr, Criterion.PLUS, is_phrase=True ) )
        else:
            # Parse <criteria>*
            while searchstr:  # until the entire string have been parsed
                sign = Criterion.PLUS  # Defaults to all criterions are mandatory
                keyword = None
                is_phrase = False

                # Parse <sign>
                m = QueryParser.SIGN_PATTERN.match( searchstr )
                if m:
                    sign = m.group(1)
                    searchstr = QueryParser.SIGN_PATTERN.sub( "", searchstr )

                # Parse <phrase>
                m = QueryParser.PHRASE_PATTERN.match( searchstr )
                if m:
                    keyword = m.group(2)
                    is_phrase = True
                    searchstr = QueryParser.PHRASE_PATTERN.sub( "", searchstr )
                # Parse <term> (if can't parse <phrase>)
                else:
                    m = QueryParser.TERM_PATTERN.match( searchstr )
                    if m:
                        keyword = m.group(1)
                        searchstr = QueryParser.TERM_PATTERN.sub( "", searchstr )

                # Check if query syntax is valid.
                if keyword:
                    # Valid syntax
                    criteria.append( Criterion( keyword, sign, is_phrase=is_phrase ) )

                elif searchstr:
                    # Invalid syntax (just use rest of $str as criteria is not empty)

                    criteria.append( Criterion( searchstr, sign, is_phrase=True ) )

                    searchstr = ""

        if exact_match:
            return criteria
        else:
            return cls.expand_query( criteria )

    @classmethod
    def expand_query( cls, criteria ):
        return criteria


class AstronomyQueryParser( QueryParser ):
    """
    Query parser than expand/narrows search criteria for use with Astronomy
    related search terms.
    """
    EXPAND_LIST = [
        '2MASS',
        'Abell',
        'AM',
        'Arp',
        'CL',
        'CRL',
        'DEM',
        'DG',
        'ESO',
        'Gliese',
        'GRO',
        'HD',
        'Henize',
        'Hen',
        'He',
        'HE',
        'HH',
        'HR',
        'HST',
        'Hubble',
        'IC',
        'IZw',
        'IRAS',
        'LHA',
        'Markarian',
        'Messier',
        'MS',
        'MyCn',
        'M',
        'NGC',
        'N',
        'PHL',
        'PKS',
        'PN',
        'PQ',
        'PSR',
        'QSO',
        'RAFGL',
        'R',
        'SMP',
        'SNR',
        'SN',
        'UCG',
        'WR',
    ]

    EXPAND_LIST_PATTERN = re.compile(r"^\s*(%s)(\s*)(\d+)\s*$" % "|".join(EXPAND_LIST), flags=re.IGNORECASE)
    EXPAND_LIST_PATTERN_PREV = re.compile(r"^(%s)$" % "|".join(EXPAND_LIST), flags=re.IGNORECASE)
    EXPAND_LIST_PATTERN_NUM = re.compile(r"(\d+)")

    @classmethod
    def expand_query( cls, criteria ):
        """
        Widening and narrowing of search criterias by expansion of query.
        """
        additional = []
        prev = ''

        criteria_copy = list(criteria)  # Make deep copy of list.

        for c in criteria_copy:
            # Expansion of a single criteria
            # Widening of search area.
            m = cls.EXPAND_LIST_PATTERN.match( c.keyword )
            if c.sign != Criterion.MINUS and m:
                chars = m.group(1)
                space = m.group(2)
                num = m.group(3)

                # Make new non-mandatory criteria.
                new_criteria = None

                if space:
                    # Expansion: "M 51" -> "M 51" "M51"
                    new_criteria = Criterion( "%s%s" % ( chars.upper(), num ), is_phrase=False, sign=Criterion.NO_SIGN )
                    # Special case: e.g "  M 51  "
                    c.keyword = "%s %s" % ( chars.upper(), num )
                    c.is_phrase = True
                else:
                    new_criteria = Criterion( "%s %s" % ( chars.upper(), num ), is_phrase=True, sign=Criterion.NO_SIGN )
                    # See above. Actually it is not necessary here.
                    c.keyword = "%s%s" % ( chars.upper(), num )
                    c.is_phrase = False

                additional.append( new_criteria )

                # Change main criteria to non-mandatory criteria
                c.sign = Criterion.NO_SIGN
                continue

            # Interpretation of multiple criteria.
            # Narrowing of search area.
            if prev:
                m = cls.EXPAND_LIST_PATTERN_NUM.match( c.keyword )
                if m:
                    num = m.group(1)

                    # Remove current and previous criteria from query
                    idx = criteria.index(c)
                    criteria.pop(idx)
                    criteria.pop(idx - 1)

                    # Add two new non-mandatory criterion based on the two removed
                    # criteria.
                    additional.append( Criterion( "%s%s" % ( prev.upper(), num ), sign=Criterion.NO_SIGN ) )
                    additional.append( Criterion( "%s %s" % ( prev.upper(), num ), is_phrase=True, sign=Criterion.NO_SIGN ) )

                prev = ''  # Reset previous state

            m = cls.EXPAND_LIST_PATTERN_PREV.match( c.keyword )
            if c.sign != Criterion.MINUS and m:
                prev = m.group(1)

        criteria += additional
        return criteria
