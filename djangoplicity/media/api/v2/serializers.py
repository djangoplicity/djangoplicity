from typing import List, Optional, TypedDict

from rest_framework import serializers
from djangoplicity.media.models import Image, Video

from djangoplicity.archives.utils import get_all_instance_archives_urls, get_instance_resources
from djangoplicity.archives.typings import ArchiveResource
from djangoplicity.utils.datetimes import timestring_to_seconds
from djangoplicity.archives.api.v2.serializers import ArchiveSerializerMixin

from djangoplicity.metadata.api.v2.serializers import CategorySerializer
from .typings import ImageFormatsURLs, VideoFormatsURLs


IMAGE__TINY_FORMATS = ['thumb300y', 'screen', 'thumb700x']
ImageTinyFormatsURLs = TypedDict('ImageFormatsURLs', dict(map(lambda x: (x, Optional[str]), IMAGE__TINY_FORMATS)))

class ImageSerializerMixin(ArchiveSerializerMixin):
    formats = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True, source='web_category')

    def get_formats(self, obj) -> ImageFormatsURLs:
        urls = get_all_instance_archives_urls(obj)
        for key, url in urls.items():
            if url and 'storage.noirlab.edu' in url:
                urls[key] = url.replace('storage.noirlab.edu', 'noirlab.edu/public')
        return urls


class VideoSerializerMixin(ArchiveSerializerMixin):
    duration = serializers.SerializerMethodField()
    formats = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True, source='web_category')

    def get_duration(self, obj) -> Optional[str]:
        return timestring_to_seconds(obj.file_duration) if obj.file_duration else None

    def get_formats(self, obj) -> VideoFormatsURLs:
        urls = get_all_instance_archives_urls(obj)
        for key, url in urls.items():
            if url and 'storage.noirlab.edu' in url:
                urls[key] = url.replace('storage.noirlab.edu', 'noirlab.edu/public')
        return urls


class ImageMiniSerializer(ImageSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'url', 'lang', 'source', 'title', 'width', 'height', 'featured', 'categories', 'formats']
        
        
class ImageTinySerializer(ArchiveSerializerMixin, serializers.ModelSerializer):
    formats = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ['id', 'url', 'lang', 'source', 'title', 'width', 'height', 'formats']

    def get_formats(self, obj) -> ImageTinyFormatsURLs:
        urls = get_all_instance_archives_urls(obj, IMAGE__TINY_FORMATS)
        for key, url in urls.items():
            if url and 'storage.noirlab.edu' in url:
                urls[key] = url.replace('storage.noirlab.edu', 'noirlab.edu/public')
        return urls


class ImageSerializer(ImageSerializerMixin, serializers.ModelSerializer):
    subject_name = serializers.StringRelatedField(many=True)
    resources = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = [
            'id', 'url', 'lang', 'source', 'title', 'headline', 'description', 'categories', 'type', 'credit',
            'release_date', 'width', 'height', 'featured', 'subject_name', 'resources', 'formats'
        ]

    def get_resources(self, obj) -> List[ArchiveResource]:
        resources = get_instance_resources(obj)
        for resource in resources:
            if resource['URL'] and 'storage.noirlab.edu' in resource['URL']:
                resource['URL'] = resource['URL'].replace('storage.noirlab.edu', 'noirlab.edu/public')
        return resources


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
