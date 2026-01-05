from djangoplicity.announcements.models import Announcement
from djangoplicity.announcements.options import AnnouncementOptions
from djangoplicity.translation.api.v2.views import TranslationAPIViewMixin, DEFAULT_API_TRANSLATION_MODE
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

from .serializers import AnnouncementMiniSerializer, AnnouncementSerializer
from rest_framework import permissions, mixins
from rest_framework.viewsets import GenericViewSet
from django_filters import rest_framework as filters


class AnnouncementPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class AnnouncementFilter(filters.FilterSet):
    program = filters.CharFilter(field_name="programs__url")
    search = filters.CharFilter(method='search_filter')
    is_e_and_e = filters.BooleanFilter(field_name="is_e_and_e")

    class Meta:
        model = Announcement
        fields = ['program','is_e_and_e']

    def search_filter(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(title__icontains=value) |
                Q(subtitle__icontains=value) |
                Q(description__icontains=value)
            )
        return queryset


class AnnouncementViewMixin:
    def get_queryset(self):
        is_e_and_e = self.request.GET.get('is_e_and_e')
        
        if is_e_and_e and is_e_and_e.lower() == 'true':
            qs, query_data = AnnouncementOptions.Queries.e_and_e.queryset(
                Announcement,
                AnnouncementOptions,
                self.request,
                mode=self.request.GET.get('translation_mode', DEFAULT_API_TRANSLATION_MODE)
            )
        else:
            qs, query_data = AnnouncementOptions.Queries.default.queryset(
                Announcement,
                AnnouncementOptions,
                self.request,
                mode=self.request.GET.get('translation_mode', DEFAULT_API_TRANSLATION_MODE)
            )

        qs = qs.select_related('announcement_type').prefetch_related('programs')

        return qs


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
            description="Search by title, subtitle, or description"
        ),
        OpenApiParameter(
            "is_e_and_e",
            OpenApiTypes.BOOL,
            description="If you select “true”, you will receive the E&E category announcements.",
            default=False 
        ),
        OpenApiParameter(
            "page_size",
            OpenApiTypes.INT,
            description=f"Number of results to return per page. Max: {AnnouncementPagination.max_page_size}, Default: {AnnouncementPagination.page_size}"
        ),
        OpenApiParameter(
            "tiny",
            OpenApiTypes.BOOL,
            description="If true returns a simplified response for the main image with minimal fields and few formats. Default: false"
        )
    ],
)
class AnnouncementListView(mixins.ListModelMixin, AnnouncementViewMixin, TranslationAPIViewMixin, GenericViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Announcement.objects.none()
    serializer_class = AnnouncementMiniSerializer
    pagination_class = AnnouncementPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = AnnouncementFilter

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Pre-fetch main visuals for better performance
        Announcement.store_main_visuals(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AnnouncementDetailView(mixins.RetrieveModelMixin, AnnouncementViewMixin, TranslationAPIViewMixin, GenericViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Announcement.objects.none()
    serializer_class = AnnouncementSerializer
