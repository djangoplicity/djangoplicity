class SatchmoSSLRedirectOverride:
    '''
    We don't use Satchmo's SSLRedirect as we only use HTTPS anyway, but we
    still need to get rid of the SSL paramers in the view
    '''
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if 'SSL' in view_kwargs:
            del view_kwargs['SSL']
