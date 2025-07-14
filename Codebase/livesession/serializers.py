"""
Serializer unifié pour la session complète de production
"""
from decimal import Decimal
from rest_framework import serializers
from core.models import Operator, FabricationOrder, Profile
from .services import ShiftMetricsService  # TODO: Rename to SessionMetricsService


class CurrentSessionSerializer(serializers.Serializer):
    """
    Serializer pour l'état complet de la session de production
    Combine les données du poste (draft) et l'état persistant
    """
    
    # === ÉTAT PERSISTANT (reste entre les postes) ===
    current_of = serializers.PrimaryKeyRelatedField(
        queryset=FabricationOrder.objects.filter(terminated=False),
        required=False,
        allow_null=True
    )
    cutting_of = serializers.PrimaryKeyRelatedField(
        queryset=FabricationOrder.objects.filter(terminated=False),
        required=False,
        allow_null=True
    )
    target_length = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=0
    )
    selected_profile = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(),
        required=False,
        allow_null=True
    )
    roll_number = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1
    )
    active_modes = serializers.JSONField(
        required=False,
        default=dict
    )
    # Métriques calculées côté client
    length_enroulable = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=0
    )
    trs_percentage = serializers.FloatField(
        required=False,
        allow_null=True,
        min_value=0,
        max_value=100
    )
    belt_speed = serializers.FloatField(
        required=False,
        allow_null=True,
        min_value=0
    )
    checklist_responses = serializers.JSONField(
        required=False,
        default=dict
    )
    checklist_signature = serializers.JSONField(
        required=False,
        allow_null=True
    )
    quality_controls = serializers.JSONField(
        required=False,
        default=dict
    )
    current_roll = serializers.JSONField(
        required=False,
        default=dict
    )
    active_productivity_tab = serializers.ChoiceField(
        choices=['temps', 'parametres'],
        required=False,
        allow_blank=True
    )
    
    # === DONNÉES DU POSTE EN COURS ===
    operator = serializers.PrimaryKeyRelatedField(
        queryset=Operator.objects.filter(is_active=True),
        required=False,
        allow_null=True
    )
    date = serializers.DateField(
        required=False,
        allow_null=True,
        error_messages={'invalid': ''}
    )
    vacation = serializers.ChoiceField(
        choices=['Matin', 'ApresMidi', 'Nuit', 'Journee'],
        required=False,
        allow_blank=True
    )
    start_time = serializers.TimeField(
        required=False,
        allow_null=True,
        format='%H:%M',
        input_formats=['%H:%M', '%H:%M:%S'],
        error_messages={'invalid': ''}
    )
    end_time = serializers.TimeField(
        required=False,
        allow_null=True,
        format='%H:%M',
        input_formats=['%H:%M', '%H:%M:%S'],
        error_messages={'invalid': ''}
    )
    
    # Machine state
    started_at_beginning = serializers.BooleanField(required=False)
    meter_reading_start = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    started_at_end = serializers.BooleanField(required=False)
    meter_reading_end = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    operator_comments = serializers.CharField(required=False, allow_blank=True)
    
    # === COLLECTIONS ===
    lost_times = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )
    
    # === MÉTRIQUES CALCULÉES ===
    metrics = serializers.SerializerMethodField()
    
    def get_metrics(self, obj):
        """Calcule toutes les métriques en temps réel"""
        # obj est maintenant juste le draft
        if isinstance(obj, dict):
            draft = obj.get('draft')
        else:
            draft = obj
            
        if draft:
            service = ShiftMetricsService(
                draft.session_data,
                session_key=self.context['request'].session.session_key
            )
            return service.get_all_metrics()
        
        return {
            'to': 0, 'to_formatted': '--',
            'tp': 0, 'tp_formatted': '--',
            'td': 0, 'td_formatted': '--',
            'length_lost': 0, 'length_lost_formatted': '--',
            'length_enroulable': 0, 'length_enroulable_formatted': '--'
        }
    
    def to_representation(self, instance):
        """Récupère toutes les données depuis CurrentSession"""
        draft = instance.get('draft')
        
        data = {}
        
        # Toutes les données sont dans la session maintenant
        if draft and draft.session_data:
            data.update(draft.session_data)
        
        # Ajouter les métriques
        data['metrics'] = self.get_metrics(instance)
        
        return data
    
    def update(self, instance, validated_data):
        """Met à jour la session - tout dans CurrentSession"""
        draft = instance.get('draft')
        
        # Tout va dans la session maintenant
        session_data = {}
        
        for key, value in validated_data.items():
            # Convertir les objets Model en ID pour le JSON
            if hasattr(value, 'pk'):
                session_data[key] = value.pk
            elif hasattr(value, 'isoformat'):  # Date/Time
                session_data[key] = value.isoformat()
            elif isinstance(value, Decimal):
                session_data[key] = float(value)
            else:
                session_data[key] = value
        
        # Mettre à jour la session
        if session_data and draft:
            draft.session_data.update(session_data)
            draft.save()
        
        return instance