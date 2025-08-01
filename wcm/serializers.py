from rest_framework import serializers
from catalog.models import WcmLostTimeReason
from .models import LostTimeEntry, Mode, MoodCounter


class WcmLostTimeReasonSerializer(serializers.ModelSerializer):
    """Serializer pour les motifs de temps perdu"""
    
    class Meta:
        model = WcmLostTimeReason
        fields = [
            'id', 'name', 'category', 'description', 
            'is_planned', 'is_active', 'order', 'color'
        ]
        read_only_fields = ['id']


class LostTimeEntrySerializer(serializers.ModelSerializer):
    """Serializer pour les entrées de temps perdu"""
    
    # Infos en lecture seule pour l'affichage
    motif_name = serializers.CharField(source='reason.name', read_only=True)
    color = serializers.CharField(source='reason.color', read_only=True)
    category = serializers.CharField(source='reason.category', read_only=True)
    
    class Meta:
        model = LostTimeEntry
        fields = [
            'id', 'reason', 'comment', 'duration', 
            'created_at', 'motif_name', 'color', 'category'
        ]
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        """Créer une entrée avec les infos de session"""
        request = self.context.get('request')
        
        # Ajouter la clé de session
        if request and hasattr(request, 'session'):
            validated_data['session_key'] = request.session.session_key
        
        # Ajouter le shift actuel s'il existe
        # TODO: Récupérer depuis la session si un shift est actif
        
        return super().create(validated_data)


class ModeSerializer(serializers.ModelSerializer):
    """Serializer pour les modes de fonctionnement"""
    
    class Meta:
        model = Mode
        fields = ['id', 'name', 'description', 'is_enabled', 'is_active']
        read_only_fields = ['id']


class MoodCounterIncrementSerializer(serializers.Serializer):
    """Serializer pour l'incrémentation du compteur d'humeur"""
    
    mood = serializers.ChoiceField(
        choices=['happy', 'neutral', 'unhappy', 'no_response'],
        required=True,
        help_text="Type d'humeur à incrémenter"
    )


class MoodCounterSerializer(serializers.ModelSerializer):
    """Serializer pour le compteur d'humeur"""
    
    class Meta:
        model = MoodCounter
        fields = ['id', 'mood_type', 'count', 'updated_at']
        read_only_fields = ['id', 'count', 'updated_at']