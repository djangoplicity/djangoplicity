from typing import Union
from djangoplicity.media.options import ImageOptions, VideoOptions
from djangoplicity.media.models import Image, Video
from djangoplicity.translation.api.v2.views import TranslationAPIViewMixin
from djangoplicity.translation.api.v2.views import DEFAULT_API_TRANSLATION_MODE
from djangoplicity.metadata.models import Facility
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, PolymorphicProxySerializer
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .serializers import ImageSerializer, ImageMiniSerializer, ImageTinySerializer, VideoSerializer, VideoMiniSerializer
from rest_framework import permissions, mixins
from rest_framework.viewsets import GenericViewSet
from django_filters import rest_framework as filters


class MediaPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class ImageFilter(filters.FilterSet):
    category = filters.CharFilter(field_name="web_category__url")
    facility = filters.ModelMultipleChoiceFilter(field_name="imageexposure__facility", queryset=Facility.objects.filter(published=True))
    search = filters.CharFilter(method='search_filter')

    class Meta:
        model = Image
        fields = ['category', 'facility']

    def search_filter(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(title__icontains=value) |
                Q(description__icontains=value) |
                Q(headline__icontains=value)
            )
        return queryset


class VideoFilter(filters.FilterSet):
    category = filters.CharFilter(field_name="web_category__url")

    class Meta:
        model = Video
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


class VideoViewMixin:
    def get_queryset(self):
        qs, query_data = VideoOptions.Queries.default.queryset(
            Video,
            VideoOptions,
            self.request,
            mode=self.request.GET.get('translation_mode', DEFAULT_API_TRANSLATION_MODE)
        )
        return qs


@extend_schema(
    parameters=[
        OpenApiParameter(
            "tiny",
            OpenApiTypes.BOOL,
            description="If true the response will be a simplified version of the image with only the minimal required fields. Default: false"
        ),
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
    responses={
        200: PolymorphicProxySerializer(
            component_name='ImageItem',
            serializers = [ImageTinySerializer, ImageMiniSerializer],
            resource_type_field_name=None
        ),
    },
)
class ImageListView(mixins.ListModelMixin, ImageViewMixin, TranslationAPIViewMixin, GenericViewSet):
    permission_classes = [permissions.AllowAny]
    # Defined in get_queryset from ImageViewMixin, this is needed for the OpenAPI schema
    queryset = Image.objects.none()
    pagination_class = MediaPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ImageFilter

    # Change serializer if we receive the parameter tiny=true
    def get_serializer_class(self) -> Union[ImageTinySerializer, ImageMiniSerializer]:
        if self.request.GET.get('tiny', 'false') == 'true':
            return ImageTinySerializer
        return ImageMiniSerializer


class ImageDetailView(mixins.RetrieveModelMixin, ImageViewMixin, TranslationAPIViewMixin, GenericViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Image.objects.none()
    serializer_class = ImageSerializer


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
class VideoListView(mixins.ListModelMixin, VideoViewMixin, TranslationAPIViewMixin, GenericViewSet):
    permission_classes = [permissions.AllowAny]
    # Defined in get_queryset from VideoViewMixin, this is needed for the OpenAPI schema
    queryset = Video.objects.none()
    serializer_class = VideoMiniSerializer
    pagination_class = MediaPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = VideoFilter


class VideoDetailView(mixins.RetrieveModelMixin, VideoViewMixin, TranslationAPIViewMixin, GenericViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Video.objects.none()
    serializer_class = VideoSerializer
