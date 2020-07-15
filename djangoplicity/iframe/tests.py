from django.test import TestCase

class IframeTestCase(TestCase):
    fixtures = ['videos.json']

    urls = [
        '/facebook/welcome/',
        '/facebook/discoveries/',
        '/facebook/virtualtours/'
    ]

    def test_url_access(self):
        for url in self.urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
