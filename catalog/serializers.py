from rest_framework import serializers
from .models import ProfileTemplate, ProfileSpecValue, ProfileParamValue, SpecItem, ParamItem, QualityDefectType


class SpecItemSerializer(serializers.ModelSerializer):
    """Serializer pour les items de spécification."""
    
    class Meta:
        model = SpecItem
        fields = ['id', 'name', 'display_name', 'unit', 'description', 'order']


class ParamItemSerializer(serializers.ModelSerializer):
    """Serializer pour les items de paramètre."""
    
    class Meta:
        model = ParamItem
        fields = ['id', 'name', 'display_name', 'category', 'unit', 'description', 'order', 'default_value']


class ProfileSpecValueSerializer(serializers.ModelSerializer):
    """Serializer pour les valeurs de spécification d'un profil."""
    spec_item = SpecItemSerializer(read_only=True)
    
    class Meta:
        model = ProfileSpecValue
        fields = [
            'id', 'spec_item', 'value_min', 'value_min_alert', 
            'value_nominal', 'value_max_alert', 'value_max', 
            'max_nok', 'is_blocking'
        ]


class ProfileParamValueSerializer(serializers.ModelSerializer):
    """Serializer pour les valeurs de paramètre d'un profil."""
    param_item = ParamItemSerializer(read_only=True)
    
    class Meta:
        model = ProfileParamValue
        fields = ['id', 'param_item', 'value']


class ProfileTemplateSerializer(serializers.ModelSerializer):
    """Serializer complet pour les profils avec toutes leurs valeurs."""
    profilespecvalue_set = ProfileSpecValueSerializer(many=True, read_only=True)
    profileparamvalue_set = ProfileParamValueSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProfileTemplate
        fields = [
            'id', 'name', 'description', 'is_active', 'is_default',
            'belt_speed_m_per_minute', 'oee_target', 'created_at', 'updated_at',
            'profilespecvalue_set', 'profileparamvalue_set'
        ]


class ProfileTemplateListSerializer(serializers.ModelSerializer):
    """Serializer léger pour la liste des profils."""
    
    class Meta:
        model = ProfileTemplate
        fields = ['id', 'name', 'description', 'is_active', 'is_default']


class QualityDefectTypeSerializer(serializers.ModelSerializer):
    """Serializer pour les types de défauts qualité."""
    
    class Meta:
        model = QualityDefectType
        fields = ['id', 'name', 'description', 'severity', 'threshold_value', 'is_active']