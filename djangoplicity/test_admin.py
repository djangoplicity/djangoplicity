from djangoplicity.test.testcases import AdminTestCase


class AdminURLSTestCase(AdminTestCase):

    urls = [
        'jsi18n/',
        'releases/releaseproxy/',
        'media/imagecomparison/',
        'auth/group/',
        'media/videobroadcastaudiotrack/',
        'reports/reportgroup/',
        'menus/menu/',
        'media/pictureoftheweekproxy/',
        'metadata/categorytype/',
        'media/videoproxy/',
        'auth/user/',
        'metadata/taggingstatus/',
        'pages/pagegroup/',
        'media/image/',
        'announcements/announcement/',
        'metadata/observationproposal/',
        'metadata/taxonomyhierarchy/',
        'metadata/facility/',
        'metadata/subjectname/',
        'metadata/publication/',
        'metadata/category/',
        'announcements/announcementtype/',
        'releases/kidsrelease/',
        'metadata/instrument/',
        'media/imagecolor/',
        'pages/embeddedpagekey/',
        'pages/page/',
        'menus/menuitem/',
        'media/videosubtitle/',
        'media/videoscript/',
        'announcements/webupdatetype/',
        'releases/release/',
        'pages/pageproxy/',
        'media/imagecomparisonproxy/',
        'media/videoaudiotrack/',
        'pages/section/',
        'releases/country/',
        'reports/report/',
        'media/video/',
        'announcements/announcementproxy/',
        'media/pictureoftheweek/',
        'media/imageproxy/',
        'announcements/webupdate/',
        'releases/releasetype/',
        'media/color/',
        'history/',
        'system/',
        'import/images/',
        'import/videos/',
        'videosubtitles/',
        'imagecomparisons/'
    ]

    def _assertExists(self, response):
        code = response.status_code
        self.assertTrue(code == 200 or code == 301)

    def test_url_access(self):
        for url in self.urls:
            response = self.client.get("/admin/%s" % url)
            print("HOLAAAAAAAAAAA\n")
            print("Testing: %s with %s" % ("/admin/%s" % url, response.status_code))
            self._assertExists(response)
