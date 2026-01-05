from djangoplicity.releases.models import Release
from djangoplicity.releases.options import ReleaseOptions
from djangoplicity.translation.api.v2.views import TranslationAPIViewMixin
from djangoplicity.translation.api.v2.views import DEFAULT_API_TRANSLATION_MODE
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from djangoplicity.archives.api.v2.config import (
    RELEASE_TYPE_PUBLIC,
    RELEASE_TYPE_STAGING,
    RELEASE_TYPE_EMBARGO,
    RELEASE_TYPE_CHOICES,
)

from .serializers import ReleaseMiniSerializer, ReleaseSerializer
from rest_framework import permissions, mixins
from rest_framework.viewsets import GenericViewSet
from django_filters import rest_framework as filters


class StagingPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return ReleaseOptions.Queries.staging.has_permissions(request)


class EmbargoPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return ReleaseOptions.Queries.embargo.has_permissions(request)


class ReleasesPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class ReleaseFilter(filters.FilterSet):
    program = filters.CharFilter(field_name="programs__url")
    search = filters.CharFilter(method='search_filter')

    class Meta:
        model = Release
        fields = ['program']

    def search_filter(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(title__icontains=value) |
                Q(subtitle__icontains=value) |
                Q(headline__icontains=value) |
                Q(description__icontains=value)
            )
        return queryset


class ReleaseViewMixin:
    def get_queryset(self):
        release_type = self.request.query_params.get('type', RELEASE_TYPE_PUBLIC)
        
        if release_type == RELEASE_TYPE_STAGING:
            query = ReleaseOptions.Queries.staging
        elif release_type == RELEASE_TYPE_EMBARGO:
            query = ReleaseOptions.Queries.embargo
        else:
            query = ReleaseOptions.Queries.default

        qs, query_data = query.queryset(
            Release,
            ReleaseOptions,
            self.request,
            mode=self.request.GET.get('translation_mode', DEFAULT_API_TRANSLATION_MODE)
        )

        qs = qs.select_related(
            'release_type',
            'kids_image',
        ).prefetch_related(
            'programs',
            'subject_category',
            'subject_name',
            'facility',
            'releasecontact_set',
            'related_images',
            'related_videos',
            'stock_images'
        )
        return qs
    
    def get_permissions(self):
        release_type = self.request.query_params.get('type', RELEASE_TYPE_PUBLIC)
        
        if release_type == RELEASE_TYPE_STAGING:
            return [StagingPermission()]
        elif release_type == RELEASE_TYPE_EMBARGO:
            return [EmbargoPermission()]
        return [permissions.AllowAny()]


@extend_schema(
    parameters=[
        OpenApiParameter(
            "program",
            OpenApiTypes.STR,
            description="The program identifier, e.g: kpno, rubin, gemini, ctio, csdc, noao, useltp, noirlab"
        ),
        OpenApiParameter(
            "search",
            OpenApiTypes.STR,
            description="Search by title, subtitle, headline or description"
        ),
        OpenApiParameter(
            "page_size",
            OpenApiTypes.INT,
            description=f"Number of results to return per page. Max: {ReleasesPagination.max_page_size}, Default: {ReleasesPagination.page_size}"
        ),
        OpenApiParameter(
            "type",
            OpenApiTypes.STR,
            enum=[t[0] for t in RELEASE_TYPE_CHOICES],
            description=f"Default: {RELEASE_TYPE_PUBLIC}"
        ),
        OpenApiParameter(
            "tiny",
            OpenApiTypes.BOOL,
            description="If true returns a simplified response for the main image with minimal fields and few formats. Default: false"
        )
    ],
)
class ReleaseListView(mixins.ListModelMixin, ReleaseViewMixin, TranslationAPIViewMixin, GenericViewSet):
    queryset = Release.objects.none()
    serializer_class = ReleaseMiniSerializer
    pagination_class = ReleasesPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ReleaseFilter

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # Pre-fetch main visuals for better performance
        Release.store_main_visuals(queryset)
        print("Precargado todo")
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema(
    parameters=[
        OpenApiParameter(
            "type",
            OpenApiTypes.STR,
            enum=[t[0] for t in RELEASE_TYPE_CHOICES],
            description=f"Default: {RELEASE_TYPE_PUBLIC}"
        ),
    ],
)
class ReleaseDetailView(mixins.RetrieveModelMixin, ReleaseViewMixin, TranslationAPIViewMixin, GenericViewSet):
    queryset = Release.objects.none()
    serializer_class = ReleaseSerializer
