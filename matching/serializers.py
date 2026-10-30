from rest_framework import serializers


class MatchParametersSerializer(serializers.Serializer):
    limit = serializers.IntegerField(default=10, min_value=1, max_value=50)
    min_score = serializers.FloatField(default=0.0, min_value=0.0, max_value=1.0)


class SearchSerializer(MatchParametersSerializer):
    query = serializers.CharField(min_length=2, max_length=500, trim_whitespace=True)
