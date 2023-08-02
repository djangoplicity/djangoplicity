from typing import Optional, TypedDict, List

from djangoplicity.utils.datetimes import timezone

from django.conf import settings
from djangoplicity.releases.models import Release, ReleaseContact
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from djangoplicity.archives.utils import related_archive_items, get_instance_archives_urls_list

from djangoplicity.archives.typings import ArchiveSerializedFormat
from djangoplicity.media.api.v2.serializers import ImageSerializer, VideoSerializer
from djangoplicity.metadata.api.v2.serializers import ProgramSerializer


class SerializedVisual(TypedDict):
    id: str
    formats: List[ArchiveSerializedFormat]


class ReleaseSerializerMixin(serializers.Serializer):
    release_date = serializers.SerializerMethodField()
    release_type = serializers.StringRelatedField()

    def get_release_date(self, obj):
        return timezone(obj.release_date, tz=settings.TIME_ZONE)


class ReleaseContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReleaseContact
        fields = [
            'name', 'email', 'telephone', 'cellular', 'affiliation',
            'address', 'city', 'state_province', 'postal_code', 'country',
        ]


class ReleaseMiniSerializer(ReleaseSerializerMixin, serializers.ModelSerializer):
    main_image = serializers.SerializerMethodField()
    programs = ProgramSerializer(many=True)

    class Meta:
        model = Release
        fields = [
            'id',
            'lang',
            'release_type',
            'title',
            'subtitle',
            'headline',
            'release_date',
            'programs',
            'main_image',
        ]

    def get_main_image(self, obj) -> Optional[SerializedVisual]:
        images = related_archive_items(Release.related_images, obj)
        # By default, related_archive_items put 'main visual' images first, then we can simply return the first one
        if images:
            return {
                "id": images[0].id,
                "formats": get_instance_archives_urls_list(images[0]),
            }


class ReleaseSerializer(ReleaseSerializerMixin, serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()
    contacts = ReleaseContactSerializer(many=True, source='releasecontact_set')
    programs = ProgramSerializer(many=True)

    class Meta:
        model = Release
        fields = [
            'id', 'lang', 'title', 'release_type', 'subtitle', 'headline', 'release_date', 'description',
            'notes', 'more_information', 'links', 'disclaimer', 'programs', 'images', 'videos', 'contacts'
        ]

    @extend_schema_field(ImageSerializer(many=True))
    def get_images(self, obj):
        images = related_archive_items(Release.related_images, obj)
        return ImageSerializer(images, many=True).data

    @extend_schema_field(VideoSerializer(many=True))
    def get_videos(self, obj):
        videos = related_archive_items(Release.related_videos, obj)
        return VideoSerializer(videos, many=True).data
