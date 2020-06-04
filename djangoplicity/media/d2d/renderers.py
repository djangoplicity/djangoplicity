# -*- coding: utf-8 -*-
#
# djangoplicity-media
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

from collections import OrderedDict

from rest_framework.renderers import JSONRenderer


AVM_TAGS = {
    'assets': 'Assets',
    'contact': 'Contact',
    'creator': 'Creator',
    'creator_url': 'URL',
    'credit': 'Credit',
    'description': 'Description',
    'observation': 'ObservationData',
    'id': 'ID',
    'priority': 'Priority',
    'reference_url': 'ReferenceURL',
    'release_date': 'PublicationDate',
    'rights': 'Rights',
    'subject': 'Subject',
    'title': 'Title',
    'type': 'Type',
}


def to_avm(data, parent=None):
    '''
    Convert the keys from the incoming dict to their respective AVM Tag names
    '''
    if isinstance(data, dict):
        new_dict = OrderedDict()
        for key, value in data.items():
            if parent == 'Collections' and key in AVM_TAGS:
                key = AVM_TAGS[key]
            new_dict[key] = to_avm(value, parent=key)
        return new_dict

    if isinstance(data, (list, tuple)):
        for i, _d in enumerate(data):
            data[i] = to_avm(data[i], parent)
        return data

    return data


class AVMJSONRenderer(JSONRenderer):
    def render(self, data, *args, **kwargs):
        return super(AVMJSONRenderer, self).render(to_avm(data), *args, **kwargs)
