# coding: utf-8
#
# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
#
from django.test import override_settings
from djangoplicity.test.base_tests import BasicTestCase
from django.http import HttpRequest
from django.template import RequestContext, Template
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'djangoplicity', 'templates'),
            os.path.join(BASE_DIR, 'test_project', 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': True,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'djangoplicity.archives.context_processors.internal_request',
            ],
        },
    },
]


class ArchiveContextProcessorTests(BasicTestCase):

    @override_settings(TEMPLATES=TEMPLATES, INTERNAL_IPS=['127.0.0.1'])
    def test_context_processors(self):
        """
        Test archive context processor, identify in a template this is INTERNAL REQUEST
        """
        request = HttpRequest()
        request.user = self.admin_user
        request.META['REMOTE_ADDR'] = '127.0.0.1'

        context = RequestContext(request, {})
        template = Template("{% if INTERNAL_REQUEST %}Is Internal{% endif %}").render(context)
        self.assertEqual(template, 'Is Internal')
