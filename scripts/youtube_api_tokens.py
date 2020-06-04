# This script is used to generate a oauth JSON file containing a renew token

from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

TOKEN_FILE = '/tmp/youtube.oauth2.json'


message = '''
If necessary create a new project at https://console.developers.google.com/project/
with the Google account you want to use.

In the sidebar on the left, expand APIs & auth. Next, click APIs. In the list
of APIs, make sure the status is ON for the YouTube Data API v3.

Click Credentials in the sidebar, then Add credentials, and OAuth 2.0 client ID.
Select Other, give it a name (e.g.: djangoplicity-media-dev), and click Create.
Then click the Download JSON icon on the right of the ID

Save the downloaded JSON file in your project conf directory, (set
YOUTUBE_CLIENT_SECRET in the settings), and use it as argument to this script
'''

YOUTUBE_SCOPE = 'https://www.googleapis.com/auth/youtube.force-ssl'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

if __name__ == '__main__':
    argparser.add_argument('--client-secret', help='Client secret JSON file',
                    required=True)

    args = argparser.parse_args()

    flow = flow_from_clientsecrets(args.client_secret,
        message=message, scope=YOUTUBE_SCOPE)

    storage = Storage(TOKEN_FILE)
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)
        print '\nToken file "%s" created' % TOKEN_FILE
    else:
        print '\nToken file "%s" already exists' % TOKEN_FILE
