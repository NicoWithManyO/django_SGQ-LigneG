from rest_framework import serializers
from catalog.models import QualityDefectType


class QualityDefectTypeSerializer(serializers.ModelSerializer):
    """Serializer pour les types de défauts qualité."""
    
    class Meta:
        model = QualityDefectType
        fields = ['id', 'name', 'description', 'severity', 'is_active']