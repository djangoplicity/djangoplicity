from djangoplicity.media.options import ImageOptions
from djangoplicity.media.models import Image, Video
from djangoplicity.translation.api.v2.views import TranslationAPIViewMixin
from djangoplicity.translation.api.v2.views import DEFAULT_API_TRANSLATION_MODE
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.pagination import PageNumberPagination

from .serializers import ImageSerializer, ImageMiniSerializer
from rest_framework import permissions, mixins
from rest_framework.viewsets import GenericViewSet
from django_filters import rest_framework as filters


class MediaPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class ImageFilter(filters.FilterSet):
    category = filters.CharFilter(field_name="web_category__url")

    class Meta:
        model = Image
        fields = ['category']


class ImageViewMixin:
    def get_queryset(self):
        qs, query_data = ImageOptions.Queries.default.queryset(
            Image,
            ImageOptions,
            self.request,
            mode=self.request.GET.get('translation_mode', DEFAULT_API_TRANSLATION_MODE)
        )
        return qs


@extend_schema(
    parameters=[
        OpenApiParameter(
            "category",
            OpenApiTypes.STR,
            description="The web category identifier, e.g: kpno, rubin, gemini, "
                        "ctio, csdc, noao, useltp, galaxies, illustrations"
        ),
        OpenApiParameter(
            "page_size",
            OpenApiTypes.INT,
            description=f"Number of results to return per page. Max: {MediaPagination.max_page_size}, Default: {MediaPagination.page_size}"
        ),
    ],
)
class ImageListView(mixins.ListModelMixin, ImageViewMixin, TranslationAPIViewMixin, GenericViewSet):
    permission_classes = [permissions.AllowAny]
    # Defined in get_queryset from ImageViewMixin, this is needed for the OpenAPI schema
    queryset = Image.objects.none()
    serializer_class = ImageMiniSerializer
    pagination_class = MediaPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ImageFilter


class ImageDetailView(mixins.RetrieveModelMixin, ImageViewMixin, TranslationAPIViewMixin, GenericViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Image.objects.none()
    serializer_class = ImageSerializer
