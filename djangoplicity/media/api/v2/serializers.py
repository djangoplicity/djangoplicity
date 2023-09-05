from typing import Optional

from rest_framework import serializers
from djangoplicity.media.models import Image, Video

from djangoplicity.archives.utils import get_all_instance_archives_urls
from djangoplicity.utils.datetimes import timestring_to_seconds
from djangoplicity.archives.api.v2.serializers import ArchiveSerializerMixin

from djangoplicity.metadata.api.v2.serializers import CategorySerializer
from .typings import ImageFormatsURLs, VideoFormatsURLs


class ImageSerializerMixin(ArchiveSerializerMixin):
    formats = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True, source='web_category')

    def get_formats(self, obj) -> ImageFormatsURLs:
        return get_all_instance_archives_urls(obj)


class VideoSerializerMixin(ArchiveSerializerMixin):
    duration = serializers.SerializerMethodField()
    formats = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True, source='web_category')

    def get_duration(self, obj) -> Optional[str]:
        return timestring_to_seconds(obj.file_duration) if obj.file_duration else None

    def get_formats(self, obj) -> VideoFormatsURLs:
        return get_all_instance_archives_urls(obj)


class ImageMiniSerializer(ImageSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'url', 'lang', 'source', 'title', 'width', 'height', 'featured', 'categories', 'formats']


class ImageSerializer(ImageSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = [
            'id', 'url', 'lang', 'source', 'title', 'headline', 'description', 'categories', 'type', 'credit',
            'release_date', 'width', 'height', 'featured', 'formats'
        ]


class VideoMiniSerializer(VideoSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = [
            'id', 'url', 'lang', 'source', 'title', 'featured', 'duration', 'categories', 'youtube_video_id',
            'use_youtube', 'formats'
        ]


class VideoSerializer(VideoSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = [
            'id', 'url', 'lang', 'source', 'title', 'headline', 'description', 'categories', 'type', 'credit',
            'release_date', 'featured', 'duration', 'youtube_video_id', 'use_youtube', 'formats'
        ]
