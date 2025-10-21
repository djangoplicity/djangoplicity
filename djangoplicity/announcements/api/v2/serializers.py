from djangoplicity.announcements.models import Announcement
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from djangoplicity.archives.utils import related_archive_items

from djangoplicity.media.api.v2.serializers import ImageMiniSerializer, VideoMiniSerializer
from djangoplicity.metadata.api.v2.serializers import ProgramSerializer
from djangoplicity.archives.api.v2.serializers import ArchiveSerializerMixin

from django.core.cache import cache
from django.conf import settings
from djangoplicity.utils.domain_rewrite import has_gemini_program_request


class AnnouncementMiniSerializer(ArchiveSerializerMixin, serializers.ModelSerializer):
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

    @extend_schema_field(ImageMiniSerializer())
    def get_main_image(self, obj):
        cache_key = f"announcement_main_image_{obj.id}"
        cache_timeout = getattr(settings, 'ANNOUNCEMENTS_CACHE_TIMEOUT', 60 * 60 * 2) # 2 hours

        cached = cache.get(cache_key)

        if cached is not None:
            return cached

        images = related_archive_items(Announcement.related_images, obj)

        if not images:
            cache.set(cache_key, None, timeout=cache_timeout) 
            return None

        # By default, related_archive_items put 'main visual' images first, then we can simply return the first one

        request = self.context.get('request')
        has_gemini_program_flag = has_gemini_program_request(request)
        context = {**self.context, 'has_gemini_program': has_gemini_program_flag}

        data = ImageMiniSerializer(images[0], context=context).data

        cache.set(cache_key, data, timeout=cache_timeout)
        return data


class AnnouncementSerializer(ArchiveSerializerMixin, serializers.ModelSerializer):
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

    @extend_schema_field(ImageMiniSerializer(many=True))
    def get_images(self, obj):
        images = related_archive_items(Announcement.related_images, obj)
        return ImageMiniSerializer(images, many=True).data        

    @extend_schema_field(VideoMiniSerializer(many=True))
    def get_videos(self, obj):
        videos = related_archive_items(Announcement.related_videos, obj)
        return VideoMiniSerializer(videos, many=True).data
