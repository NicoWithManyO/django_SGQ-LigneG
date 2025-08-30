from rest_framework import serializers

class SessionSerializer(serializers.Serializer):
    """Serializer pour gérer les données de session."""
    
    # Profil sélectionné
    profile_id = serializers.IntegerField(required=False, allow_null=True)
    belt_speed_mpm = serializers.DecimalField(max_digits=6, decimal_places=2, required=False, allow_null=True)
    modes = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    
    # Données du poste
    shift_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    operator_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)  # employee_id est un string
    shift_date = serializers.DateField(required=False, allow_null=True)
    vacation = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    start_time = serializers.TimeField(required=False, allow_null=True)
    end_time = serializers.TimeField(required=False, allow_null=True)
    
    # États machine
    machine_started_start = serializers.BooleanField(required=False, allow_null=True)
    machine_started_end = serializers.BooleanField(required=False, allow_null=True)
    length_start = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    length_end = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    # Commentaire
    comment = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    # Ordre de fabrication
    of_en_cours = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    target_length = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    of_decoupe = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    # Sticky bar - Données du rouleau
    roll_number = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    tube_mass = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    roll_length = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    total_mass = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    next_tube_mass = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    # Sticky bar V2 fields
    current_roll_number = serializers.IntegerField(required=False, allow_null=True)
    current_roll_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    current_roll_tube_mass = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    current_roll_length = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    current_roll_total_mass = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    current_roll_thicknesses = serializers.JSONField(required=False, allow_null=True)
    next_tube_weight = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    
    # V2 shift form fields
    shift_form_machine_started_start = serializers.BooleanField(required=False, allow_null=True)
    shift_form_machine_started_end = serializers.BooleanField(required=False, allow_null=True)
    shift_form_length_start = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    shift_form_length_end = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    shift_form_start_time = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    shift_form_end_time = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    # Données du rouleau (épaisseurs et défauts)
    roll_data = serializers.JSONField(required=False, allow_null=True)
    roll_measurements = serializers.JSONField(required=False, allow_null=True)
    roll_defects = serializers.JSONField(required=False, allow_null=True)
    roll_thickness_stats = serializers.JSONField(required=False, allow_null=True)
    roll_defect_counts = serializers.JSONField(required=False, allow_null=True)
    roll_conformity = serializers.JSONField(required=False, allow_null=True)
    
    # Données checklist
    checklist_responses = serializers.JSONField(required=False, allow_null=True)
    checklist_signature = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    checklist_signature_time = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    # Contrôle qualité
    quality_control = serializers.JSONField(required=False, allow_null=True)
    
    # Temps perdus
    lost_time_entries = serializers.JSONField(required=False, allow_null=True)
    temps_total = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    has_startup_time = serializers.BooleanField(required=False, allow_null=True)
    
    # Compteurs de production (longueurs enroulées)
    wound_length_ok = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    wound_length_nok = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    wound_length_total = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    
    def update(self, instance, validated_data):
        """Met à jour la session avec les données validées."""
        # instance = request.session
        
        # Convertir les Decimal en float pour éviter les erreurs de sérialisation
        decimal_fields = [
            'wound_length_ok', 'wound_length_nok', 'wound_length_total', 'belt_speed_mpm',
            'current_roll_tube_mass', 'current_roll_length', 'current_roll_total_mass', 'next_tube_weight'
        ]
        for key in decimal_fields:
            if key in validated_data and validated_data[key] is not None:
                validated_data[key] = float(validated_data[key])
        for key, value in validated_data.items():
            if value is None:
                # Supprimer de la session si None
                instance.pop(key, None)
            else:
                # Convertir les dates et heures en string pour la session
                if key == 'shift_date' and value:
                    instance[key] = value.isoformat()
                elif key in ['start_time', 'end_time'] and value:
                    instance[key] = value.strftime('%H:%M')
                else:
                    instance[key] = value
        instance.save()  # Important pour persister
        return instance