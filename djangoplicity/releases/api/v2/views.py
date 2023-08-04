from djangoplicity.releases.models import Release
from djangoplicity.releases.options import ReleaseOptions
from djangoplicity.translation.api.v2.views import TranslationAPIViewMixin
from djangoplicity.translation.api.v2.views import DEFAULT_API_TRANSLATION_MODE
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.pagination import PageNumberPagination

from .serializers import ReleaseMiniSerializer, ReleaseSerializer
from rest_framework import permissions, mixins
from rest_framework.viewsets import GenericViewSet
from django_filters import rest_framework as filters


class ReleasesPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class ReleaseFilter(filters.FilterSet):
    program = filters.CharFilter(field_name="programs__url")

    class Meta:
        model = Release
        fields = ['program']


class ReleaseViewMixin:
    def get_queryset(self):
        qs, query_data = ReleaseOptions.Queries.default.queryset(
            Release,
            ReleaseOptions,
            self.request,
            mode=self.request.GET.get('translation_mode', DEFAULT_API_TRANSLATION_MODE)
        )
        return qs


@extend_schema(
    parameters=[
        OpenApiParameter(
            "program",
            OpenApiTypes.STR,
            description="The program identifier, e.g: kpno, rubin, gemini, ctio, csdc, noao, useltp, noirlab"
        ),
        OpenApiParameter(
            "page_size",
            OpenApiTypes.INT,
            description=f"Number of results to return per page. Max: {ReleasesPagination.max_page_size}, Default: {ReleasesPagination.page_size}"
        ),
    ],
)
class ReleaseListView(mixins.ListModelMixin, ReleaseViewMixin, TranslationAPIViewMixin, GenericViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Release.objects.none()
    serializer_class = ReleaseMiniSerializer
    pagination_class = ReleasesPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ReleaseFilter


class ReleaseDetailView(mixins.RetrieveModelMixin, ReleaseViewMixin, TranslationAPIViewMixin, GenericViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Release.objects.none()
    serializer_class = ReleaseSerializer
