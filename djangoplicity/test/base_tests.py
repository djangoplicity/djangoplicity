from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.test.testcases import TransactionTestCase

try:
    from mock import patch, MagicMock
except ImportError:
    from unittest.mock import patch, MagicMock


class BasicTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@newsletters.org',
            password='password123'
        )
        self.client.force_login(self.admin_user)


class BaseContactTestCase(TransactionTestCase):
    """
    Base Contact class
    """

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@newsletters.org',
            password='password123'
        )
        self.client.force_login(self.admin_user)
