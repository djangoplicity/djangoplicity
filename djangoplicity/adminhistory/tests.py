# -*- coding: utf-8 -*-
#
# djangoplicity-adminhistory
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
from django.contrib.contenttypes.models import ContentType

from djangoplicity.test.base_tests import BasicTestCase
from django.contrib.admin.models import LogEntry


class AdminHistoryTestCase(BasicTestCase):

    def setUp(self):
        super(AdminHistoryTestCase, self).setUp()
        data = {
            'action_flag': 1,
            'change_message': u'[{"added": {}}]',
            'content_type': ContentType.objects.get(model='user'),
            'id': self.admin_user.id,
            'object_id': u'7',
            'object_repr': 'User object',
            'user': self.admin_user
        }
        entry = LogEntry.objects.create(**data)
        entry.save()

    def test_adminhistory_index(self):
        response = self.client.get('/admin/history/?s=user&u=5')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/admin/history/?s=user&u=5&p=x')
        self.assertEqual(response.status_code, 200)
