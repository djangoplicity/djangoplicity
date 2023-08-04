from djangoplicity.utils.datetimes import timezone
from django.contrib.sites.models import Site

from django.conf import settings
from djangoplicity.releases.models import Release, ReleaseContact
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from djangoplicity.archives.utils import related_archive_items, get_all_instance_archives_urls

from djangoplicity.media.api.v2.serializers import ImageSerializer, VideoSerializer
from djangoplicity.metadata.api.v2.serializers import ProgramSerializer


class ReleaseSerializerMixin(serializers.Serializer):
    release_date = serializers.SerializerMethodField()
    release_type = serializers.StringRelatedField()
    url = serializers.SerializerMethodField()

    def get_release_date(self, obj):
        return timezone(obj.release_date, tz=settings.TIME_ZONE)

    def get_url(self, obj):
        return f"https://{Site.objects.get_current().domain}{obj.get_absolute_url()}"


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
            'url',
            'release_type',
            'title',
            'subtitle',
            'headline',
            'release_date',
            'programs',
            'main_image',
        ]

    @extend_schema_field(ImageSerializer)
    def get_main_image(self, obj):
        images = related_archive_items(Release.related_images, obj)
        # By default, related_archive_items put 'main visual' images first, then we can simply return the first one
        if images:
            return ImageSerializer(images[0]).data


class ReleaseSerializer(ReleaseSerializerMixin, serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()
    contacts = ReleaseContactSerializer(many=True, source='releasecontact_set')
    programs = ProgramSerializer(many=True)

    class Meta:
        model = Release
        fields = [
            'id', 'lang', 'url', 'title', 'release_type', 'subtitle', 'headline', 'release_date', 'description',
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
