from django.test import TestCase

class EventcalendarTestCase(TestCase):
    fixtures = ['events.json']

    def test_url_access(self):
        response = self.client.get('/eventcalendar/science/')
        self.assertEqual(response.status_code, 200)
