from rest_framework import serializers
from django.db import transaction
from .models import Roll, Shift
from quality.models import RollThickness, RollDefect
from catalog.models import QualityDefectType
from wcm.models import ChecklistResponse


class RollThicknessSerializer(serializers.ModelSerializer):
    """Serializer pour les mesures d'épaisseur."""
    
    class Meta:
        model = RollThickness
        fields = [
            'meter_position', 
            'measurement_point',
            'thickness_value',
            'is_catchup',
            'is_within_tolerance'
        ]
        
    def validate_measurement_point(self, value):
        """Valide que le point de mesure est valide."""
        valid_points = ['GG', 'GC', 'GD', 'DG', 'DC', 'DD']
        if value not in valid_points:
            raise serializers.ValidationError(
                f"Point de mesure invalide. Doit être parmi : {', '.join(valid_points)}"
            )
        return value


class RollDefectSerializer(serializers.ModelSerializer):
    """Serializer pour les défauts du rouleau."""
    
    defect_type_id = serializers.PrimaryKeyRelatedField(
        queryset=QualityDefectType.objects.filter(is_active=True),
        source='defect_type'
    )
    
    class Meta:
        model = RollDefect
        fields = [
            'defect_type_id',
            'meter_position',
            'side_position',
            'comment'
        ]
    
    def validate_side_position(self, value):
        """Valide que la position est correcte."""
        valid_positions = ['GG', 'GC', 'GD', 'DG', 'DC', 'DD']
        if value not in valid_positions:
            raise serializers.ValidationError(
                f"Position invalide '{value}'. Doit être parmi : {', '.join(valid_positions)}"
            )
        return value


class RollSerializer(serializers.ModelSerializer):
    """Serializer principal pour les rouleaux."""
    
    thicknesses = RollThicknessSerializer(many=True, required=False)
    defects = RollDefectSerializer(many=True, required=False)
    shift_id_str = serializers.CharField(required=True, write_only=True)
    
    # Champs calculés en lecture seule
    net_mass = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    grammage_calc = serializers.DecimalField(
        max_digits=7,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = Roll
        fields = [
            'id',
            'roll_id',
            'roll_number',
            'fabrication_order',
            'shift_id_str',
            'length',
            'tube_mass',
            'total_mass',
            'net_mass',
            'grammage_calc',
            'status',
            'destination',
            'has_blocking_defects',
            'has_thickness_issues',
            'avg_thickness_left',
            'avg_thickness_right',
            'comment',
            'thicknesses',
            'defects',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'net_mass',
            'grammage_calc', 
            'has_blocking_defects',
            'has_thickness_issues',
            'avg_thickness_left',
            'avg_thickness_right',
            'created_at',
            'updated_at'
        ]
    
    def validate(self, attrs):
        """Validation globale du rouleau."""
        # Validation masse totale > masse tube
        total_mass = attrs.get('total_mass')
        tube_mass = attrs.get('tube_mass')
        
        if total_mass and tube_mass and total_mass <= tube_mass:
            raise serializers.ValidationError({
                'total_mass': 'La masse totale doit être supérieure à la masse du tube.'
            })
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        """Création du rouleau avec ses relations."""
        # Extraire les données nested
        thicknesses_data = validated_data.pop('thicknesses', [])
        defects_data = validated_data.pop('defects', [])
        
        # Les champs de session seront ajoutés dans la vue
        # pour respecter la séparation des responsabilités
        
        # Créer le rouleau
        roll = Roll.objects.create(**validated_data)
        
        # Créer les épaisseurs
        for thickness_data in thicknesses_data:
            RollThickness.objects.create(roll=roll, **thickness_data)
        
        # Créer les défauts
        for defect_data in defects_data:
            RollDefect.objects.create(roll=roll, **defect_data)
        
        return roll
    
    def to_representation(self, instance):
        """Représentation du rouleau avec ses relations."""
        data = super().to_representation(instance)
        
        # Inclure les épaisseurs
        data['thicknesses'] = RollThicknessSerializer(
            instance.thickness_measurements.all(),
            many=True
        ).data
        
        # Inclure les défauts
        data['defects'] = RollDefectSerializer(
            instance.defects.all(),
            many=True
        ).data
        
        return data


class ChecklistResponseSerializer(serializers.ModelSerializer):
    """Serializer pour les réponses de checklist."""
    
    class Meta:
        model = ChecklistResponse
        fields = [
            'responses',
            'operator_signature',
            'operator_signature_date',
            'management_visa',
            'management_visa_date',
            'created_at'
        ]
        read_only_fields = ['created_at']


class ShiftSerializer(serializers.ModelSerializer):
    """Serializer principal pour les postes."""
    
    checklist_response = ChecklistResponseSerializer(read_only=True)
    operator_name = serializers.CharField(source='operator.full_name', read_only=True)
    
    # Statistiques calculées
    roll_count = serializers.IntegerField(read_only=True)
    total_lost_time_minutes = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Shift
        fields = [
            'id',
            'shift_id',
            'date',
            'operator',
            'operator_name',
            'vacation',
            'start_time',
            'end_time',
            'availability_time',
            'lost_time',
            'total_length',
            'ok_length',
            'nok_length',
            'raw_waste_length',
            'avg_thickness_left_shift',
            'avg_thickness_right_shift',
            'avg_grammage_shift',
            'started_at_beginning',
            'meter_reading_start',
            'started_at_end',
            'meter_reading_end',
            'checklist_signed',
            'checklist_signed_time',
            'operator_comments',
            'checklist_response',
            'roll_count',
            'total_lost_time_minutes',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'shift_id',  # Généré automatiquement
            'availability_time',
            'lost_time',
            'total_length',
            'ok_length',
            'nok_length',
            'raw_waste_length',
            'avg_thickness_left_shift',
            'avg_thickness_right_shift',
            'avg_grammage_shift',
            'roll_count',
            'total_lost_time_minutes',
            'created_at',
            'updated_at'
        ]
    
    def validate(self, attrs):
        """Validation globale du poste."""
        # Vérifier la cohérence des heures (sauf pour vacation Nuit)
        vacation = attrs.get('vacation')
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        
        if vacation != 'Nuit' and start_time and end_time:
            if start_time >= end_time:
                raise serializers.ValidationError({
                    'end_time': "L'heure de fin doit être après l'heure de début (sauf vacation Nuit)."
                })
        
        # Vérifier la cohérence machine/métrage
        started_at_beginning = attrs.get('started_at_beginning')
        meter_reading_start = attrs.get('meter_reading_start')
        
        if started_at_beginning and meter_reading_start is None:
            raise serializers.ValidationError({
                'meter_reading_start': 'Le métrage de début est requis si la machine était démarrée.'
            })
        
        started_at_end = attrs.get('started_at_end')
        meter_reading_end = attrs.get('meter_reading_end')
        
        if started_at_end and meter_reading_end is None:
            raise serializers.ValidationError({
                'meter_reading_end': 'Le métrage de fin est requis si la machine était démarrée.'
            })
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        """Création du poste avec ses relations."""
        # La création des ChecklistResponse est gérée dans services.py
        # via create_shift_from_session() pour avoir accès aux données de session
        
        # Créer le poste
        shift = Shift.objects.create(**validated_data)
        
        return shift