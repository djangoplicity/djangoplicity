from rest_framework import serializers
from djangoplicity.utils.datetimes import timezone
from django.conf import settings
from django.contrib.sites.models import Site


class ArchiveSerializerMixin(serializers.Serializer):
    url = serializers.SerializerMethodField()
    release_date = serializers.SerializerMethodField()

    def get_release_date(self, obj):
        return timezone(obj.release_date, tz=settings.TIME_ZONE)

    def get_url(self, obj):
        return f"https://{Site.objects.get_current().domain}{obj.get_absolute_url()}"

