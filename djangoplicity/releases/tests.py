from django.test import TestCase
from djangoplicity.releases.options import ReleaseOptions

class ReleasesTestCase(TestCase):
    conf = {
        'releases': {
            'root': '/news/',
            'options': ReleaseOptions,
            'list_views': [
                ('embargo', '', 302),
                ('search', '', 302),
                ('staging', '', 302),
                ('year', '2020/', 200),
            ]
        }
    }

    def test_index_root(self):
        response = self.client.get('/news/')
        self.assertEqual(response.status_code, 200)

    def test_queries(self):
        for conf in self.conf.values():
            options = conf['options']
            root = conf['root']
            views = conf['list_views']

            for query, subpart, code in views:
                view_url_root = "%sarchive/%s/%s" % (root, query, subpart)
                response = self.client.get(view_url_root)
                print('!!!!!!!!!!!!!!!!!!!!')
                print("testing: %s with %s" % (view_url_root, response.status_code))
                print("???????????????????")
                self.assertEqual(response.status_code, code)

                for browser in getattr(options.Queries, query).browsers:
                    view_url = "%s%s/" % (view_url_root, browser)
                    response = self.client.get(view_url)
                    self.assertEqual(response.status_code, code)
