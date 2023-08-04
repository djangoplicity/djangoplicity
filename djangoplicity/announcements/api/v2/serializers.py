from django.contrib.sites.models import Site
from djangoplicity.utils.datetimes import timezone

from django.conf import settings
from djangoplicity.announcements.models import Announcement
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from djangoplicity.archives.utils import related_archive_items

from djangoplicity.media.api.v2.serializers import ImageSerializer, VideoSerializer
from djangoplicity.metadata.api.v2.serializers import ProgramSerializer


class AnnouncementSerializerMixin(serializers.Serializer):
    release_date = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    def get_release_date(self, obj):
        return timezone(obj.release_date, tz=settings.TIME_ZONE)

    def get_url(self, obj):
        return f"https://{Site.objects.get_current().domain}{obj.get_absolute_url()}"


class AnnouncementMiniSerializer(AnnouncementSerializerMixin, serializers.ModelSerializer):
    main_image = serializers.SerializerMethodField()
    programs = ProgramSerializer(many=True)

    class Meta:
        model = Announcement
        fields = [
            'id',
            'lang',
            'url',
            'title',
            'subtitle',
            'release_date',
            'programs',
            'main_image',
        ]

    @extend_schema_field(ImageSerializer())
    def get_main_image(self, obj):
        images = related_archive_items(Announcement.related_images, obj)
        # By default, related_archive_items put 'main visual' images first, then we can simply return the first one
        if images:
            return ImageSerializer(images[0]).data


class AnnouncementSerializer(AnnouncementSerializerMixin, serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()
    programs = ProgramSerializer(many=True)

    class Meta:
        model = Announcement
        fields = [
            'id',
            'lang',
            'url',
            'title',
            'subtitle',
            'description',
            'contacts',
            'links',
            'featured',
            'release_date',
            'programs',
            'images',
            'videos',
        ]

    @extend_schema_field(ImageSerializer(many=True))
    def get_images(self, obj):
        images = related_archive_items(Announcement.related_images, obj)
        return ImageSerializer(images, many=True).data

    @extend_schema_field(VideoSerializer(many=True))
    def get_videos(self, obj):
        videos = related_archive_items(Announcement.related_videos, obj)
        return VideoSerializer(videos, many=True).data
