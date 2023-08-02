from djangoplicity.metadata.models import Program
from rest_framework import serializers


class ProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
        fields = [
            'url',
            'name',
            'logo_url'
        ]

