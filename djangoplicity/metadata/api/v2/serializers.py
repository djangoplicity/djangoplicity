from djangoplicity.metadata.models import Program
from rest_framework import serializers


class ProgramSerializer(serializers.ModelSerializer):
    slug = serializers.CharField(source='url')

    class Meta:
        model = Program
        fields = [
            'slug',
            'name',
            'logo_url'
        ]
