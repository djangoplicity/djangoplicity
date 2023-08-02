from djangoplicity.announcements.models import Announcement
from djangoplicity.announcements.options import AnnouncementOptions
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.pagination import PageNumberPagination

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

    class Meta:
        model = Announcement
        fields = ['program']


class ReleaseViewMixin:
    def get_queryset(self):
        qs, query_data = AnnouncementOptions.Queries.default.queryset(Announcement, AnnouncementOptions, self.request)
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
            description=f"Number of results to return per page. Max: {AnnouncementPagination.max_page_size}, Default: {AnnouncementPagination.page_size}"
        ),
    ],
)
class AnnouncementListView(mixins.ListModelMixin, ReleaseViewMixin, GenericViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Announcement.objects.none()
    serializer_class = AnnouncementMiniSerializer
    pagination_class = AnnouncementPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = AnnouncementFilter


class AnnouncementDetailView(mixins.RetrieveModelMixin, ReleaseViewMixin, GenericViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Announcement.objects.none()
    serializer_class = AnnouncementSerializer


