from djangoplicity.releases.models import Release, ReleaseContact
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from djangoplicity.archives.utils import related_archive_items, get_all_instance_archives_urls

from djangoplicity.media.api.v2.serializers import ImageMiniSerializer, VideoMiniSerializer, ImageTinySerializer
from djangoplicity.metadata.api.v2.serializers import ProgramSerializer
from djangoplicity.archives.api.v2.serializers import ArchiveSerializerMixin

from django.core.cache import cache
from django.conf import settings
from djangoplicity.utils.domain_rewrite import has_gemini_program_request


class ReleaseSerializerMixin(ArchiveSerializerMixin):
    release_type = serializers.StringRelatedField()


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

    @extend_schema_field(ImageMiniSerializer())
    def get_main_image(self, obj):
        request = self.context.get('request')
        has_gemini_program_flag = has_gemini_program_request(request)
        has_tiny_param = request and request.query_params.get('tiny') == 'true'

        context = {**self.context, 'has_gemini_program': has_gemini_program_flag}
        serializer_class = ImageTinySerializer if has_tiny_param else ImageMiniSerializer

        if hasattr(obj, '_main_image_cache'):
            main_image = obj._main_image_cache
        else:
            images = related_archive_items(Release.related_images, obj)
            main_image = images[0] if images else None
        
        if not main_image:
            return None
        
        return serializer_class(main_image, context=context).data


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

    @extend_schema_field(ImageMiniSerializer(many=True))
    def get_images(self, obj):
        images = related_archive_items(Release.related_images, obj)
        return ImageMiniSerializer(images, many=True).data

    @extend_schema_field(VideoMiniSerializer(many=True))
    def get_videos(self, obj):
        videos = related_archive_items(Release.related_videos, obj)
        return VideoMiniSerializer(videos, many=True).data
