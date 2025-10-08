from djangoplicity.announcements.models import Announcement
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from djangoplicity.archives.utils import related_archive_items

from djangoplicity.media.api.v2.serializers import ImageMiniSerializer, VideoMiniSerializer
from djangoplicity.metadata.api.v2.serializers import ProgramSerializer
from djangoplicity.archives.api.v2.serializers import ArchiveSerializerMixin

from djangoplicity.utils.domain_rewrite import has_gemini_program


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
        images = related_archive_items(Announcement.related_images, obj)
        # By default, related_archive_items put 'main visual' images first, then we can simply return the first one
        if images:
            has_gemini_program_flag = has_gemini_program(obj.programs.all())
            context = {**self.context, 'has_gemini_program': has_gemini_program_flag}

            return ImageMiniSerializer(images[0], context=context).data


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

        has_gemini_program_flag = has_gemini_program(obj.programs.all())
        context = {**self.context, 'has_gemini_program': has_gemini_program_flag}
        
        return ImageMiniSerializer(images, many=True, context=context).data

    @extend_schema_field(VideoMiniSerializer(many=True))
    def get_videos(self, obj):
        videos = related_archive_items(Announcement.related_videos, obj)

        has_gemini_program_flag = has_gemini_program(obj.programs.all())
        context = {**self.context, 'has_gemini_program': has_gemini_program_flag}

        return VideoMiniSerializer(videos, many=True, context=context).data
