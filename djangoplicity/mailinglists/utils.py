# -*- coding: utf-8 -*-
#
# djangoplicity-newsletters
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


import re


class DataQueryParser(object):
    '''
    Parse incoming POST or GET parameters into a dictionary. Example::

    >>> DataQueryParser.parse({
    ....    "data[merges][GROUPINGS][0][name]"  : "Tick the category you qualify for:",
    ....    "data[merges][GROUPINGS][0][id]" : "1",
    ....})
    {u'merges': {u'GROUPINGS': [{u'id': u'1', u'name': u'Tick the category you qualify for:'}]}}

    This is similar to PHP's style of parsing of query strings. This is however only used
    for MailChimp webhooks incoming data.
    '''

    @staticmethod
    def parse(querydict):
        '''
        Algorithm:

            1) Generate a trail like ('merges','GROUPINGS','0','name')
            2) Follow trail into the dictionary and set the value dict['merges']['GROUPINGS'][0]['name'] = val
        '''
        queryvars = {}
        for k, v in querydict.items():
            trail = DataQueryParser._parse_key(k)
            if trail and len(trail) > 0:
                DataQueryParser._set_value(queryvars, trail, v)
        return queryvars

    @staticmethod
    def _parse_key(k):
        '''
        Parse the query key - e.g. data[merges][GROUPINGS][0][id]
        '''
        def parse_key2(k, regexp=re.compile(r'^\[([a-zA-Z0-9_]+)\]')):
            m = regexp.search(k)
            if m:
                return [m.group(1)] + parse_key2(k[len(m.group(0)):])
            else:
                return []

        return parse_key2(k, regexp=re.compile(r'^data\[([a-zA-Z0-9_]+)\]'))

    @staticmethod
    def _set_value(qdict, trail, val):
        '''
        Set the query value using the found trail.
        '''
        if len(trail) == 1:
            if isinstance(qdict, dict):
                qdict[trail[0]] = val
            else:
                qdict[int(trail[0])] = val
        else:
            if isinstance(qdict, dict):
                if trail[0] not in qdict:
                    try:
                        int(trail[1])
                        qdict[trail[0]] = []
                    except ValueError:
                        qdict[trail[0]] = {}
                DataQueryParser._set_value(qdict[trail[0]], trail[1:], val)
            else:
                try:
                    idx = int(trail[0])
                    qdict[idx]
                except IndexError:
                    try:
                        int(trail[1])
                        qdict[idx] = []
                    except ValueError:
                        qdict.insert(idx, {})

                DataQueryParser._set_value(qdict[idx], trail[1:], val)
