from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.viewsets import GenericViewSet

from django.conf import settings


DEFAULT_API_TRANSLATION_MODE = 'language'


@extend_schema(
    parameters=[
        OpenApiParameter(
            "lang",
            OpenApiTypes.STR,
            enum=[lang[0] for lang in settings.LANGUAGES],
            description=f'The language to use, used along with "translation_mode", default: user "preferred_language"'
        ),
        OpenApiParameter(
            "translation_mode",
            OpenApiTypes.STR,
            enum=["language", "fallback"],
            description='Defines if the original version of an object is returned in case the translation is not found,'
                        ' use "fallback" to retrieve the original content if no translation exist, or'
                        f' "language" to return translated content only. Default: "{DEFAULT_API_TRANSLATION_MODE}"'
        ),
    ],
)
# Extend this Mixin to append these parameters to the API endpoints schema,
# and follow the recommended implementation of get_queryset
class TranslationAPIViewMixin(GenericViewSet):
    pass

    # Example get_queryset (The "lang" parameter is read automatically by the DP middleware)
    '''
    def get_queryset(self):
        qs, query_data = ReleaseOptions.Queries.default.queryset(
            Release,
            ReleaseOptions,
            self.request,
            mode=self.request.GET.get('translation_mode', DEFAULT_API_TRANSLATION_MODE)
        )
        return qs
    '''
