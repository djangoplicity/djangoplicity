from typing import List

from rest_framework import serializers
from djangoplicity.media.models import Image, Video

from djangoplicity.archives.utils import get_instance_archives_urls_list
from djangoplicity.archives.typings import ArchiveSerializedFormat


class ImageSerializer(serializers.ModelSerializer):
    formats = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ['id', 'source', 'title', 'width', 'height', 'featured', 'formats']

    def get_formats(self, obj) -> List[ArchiveSerializedFormat]:
        return get_instance_archives_urls_list(obj)


class VideoSerializer(serializers.ModelSerializer):
    formats = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['id', 'source', 'title', 'featured', 'file_duration', 'youtube_video_id', 'use_youtube', 'formats']

    def get_formats(self, obj) -> List[ArchiveSerializedFormat]:
        return get_instance_archives_urls_list(obj)
