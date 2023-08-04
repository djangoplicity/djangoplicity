from typing import Optional

from django.contrib.sites.models import Site
from rest_framework import serializers
from djangoplicity.media.models import Image, Video

from djangoplicity.archives.utils import get_all_instance_archives_urls
from djangoplicity.utils.datetimes import timestring_to_seconds

from .typings import ImageFormatsURLs, VideoFormatsURLs


class ImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    formats = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ['id', 'url', 'source', 'title', 'width', 'height', 'featured', 'formats']

    def get_url(self, obj):
        return f"https://{Site.objects.get_current().domain}{obj.get_absolute_url()}"

    def get_formats(self, obj) -> ImageFormatsURLs:
        return get_all_instance_archives_urls(obj)


class VideoSerializer(serializers.ModelSerializer):
    formats = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['id', 'url', 'source', 'title', 'featured', 'duration', 'youtube_video_id', 'use_youtube', 'formats']

    def get_url(self, obj):
        return f"https://{Site.objects.get_current().domain}{obj.get_absolute_url()}"

    def get_formats(self, obj) -> VideoFormatsURLs:
        return get_all_instance_archives_urls(obj)

    def get_duration(self, obj) -> Optional[str]:
        return timestring_to_seconds(obj.file_duration) if obj.file_duration else None
