from django.db import models
from django.contrib.auth.models import User


class CurrentProductionState(models.Model):
    """Données persistantes entre les postes - préférences utilisateur"""
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    
    # OF et paramètres qui restent entre les sessions
    current_of = models.ForeignKey('core.FabricationOrder', null=True, blank=True, on_delete=models.SET_NULL)
    cutting_of = models.ForeignKey('core.FabricationOrder', null=True, blank=True, related_name='cutting_sessions', on_delete=models.SET_NULL)
    target_length = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Profil et modes actifs
    selected_profile = models.ForeignKey('core.Profile', null=True, blank=True, on_delete=models.SET_NULL)
    active_modes = models.JSONField(default=dict)  # {"maintenance": true, "permissive": false}
    
    # Onglet actif dans le bloc productivité
    active_productivity_tab = models.CharField(
        max_length=20,
        default='temps',
        choices=[('temps', 'TRS'), ('parametres', 'Params & Specs')],
        verbose_name="Onglet actif productivité"
    )
    
    # Numéro de rouleau persistant
    roll_number = models.PositiveIntegerField(
        null=True, 
        blank=True,
        verbose_name="Numéro de rouleau actuel"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'livesession_current_state'
        verbose_name = 'État de production persistant'
        verbose_name_plural = 'États de production persistants'
    
    def __str__(self):
        return f"Session {self.session_key[:8]}... - {self.updated_at.strftime('%d/%m %H:%M')}"


class LiveShift(models.Model):
    """Draft du poste en cours de saisie - données temporaires"""
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    
    # Tout ce qui concerne le poste actuel en JSON
    shift_data = models.JSONField(default=dict)
    # Structure attendue:
    # {
    #     "operator_id": 1,
    #     "date": "2024-01-15", 
    #     "vacation": "Matin",
    #     "start_time": "06:00",
    #     "end_time": "14:00",
    #     "quality_controls": {...},
    #     "rolls": [...],
    #     "lost_times": [...],
    #     "checklist": {...}
    # }
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'livesession_live_shift'
        verbose_name = 'Brouillon de poste'
        verbose_name_plural = 'Brouillons de postes'
    
    def __str__(self):
        # Le champ est stocké comme 'operator' (pas 'operator_name')
        # Si c'est un ID, essayer de récupérer le nom de l'opérateur
        operator_value = self.shift_data.get('operator', 'Sans opérateur')
        
        # Si la valeur ressemble à un ID (nombre), essayer de récupérer le nom
        if operator_value and str(operator_value).isdigit():
            try:
                from core.models import Operator
                operator_obj = Operator.objects.get(pk=int(operator_value))
                operator_name = operator_obj.full_name
            except:
                operator_name = f"Opérateur #{operator_value}"
        else:
            operator_name = operator_value or 'Sans opérateur'
            
        date = self.shift_data.get('date', 'Sans date')
        return f"Draft: {operator_name} - {date}"


class LiveRoll(models.Model):
    """Brouillon de rouleau en cours de saisie - données temporaires"""
    session_key = models.CharField(max_length=40, db_index=True)
    
    # Tout ce qui concerne le rouleau actuel en JSON
    roll_data = models.JSONField(default=dict)
    # Structure attendue:
    # {
    #     "roll_id": "OF123_001",
    #     "fabrication_order_id": 1,
    #     "is_compliant": true,
    #     "avg_thickness_left": 2.5,
    #     "avg_thickness_right": 2.6,
    #     "net_mass": 450.5,
    #     "comment": "RAS",
    #     "defects": [
    #         {"type_id": 1, "position_m": 150, "position_side": "G"}
    #     ],
    #     "thickness_measurements": [
    #         {"position_m": 100, "thickness_left": 2.5, "thickness_right": 2.6}
    #     ]
    # }
    
    # Flag pour savoir si c'est le rouleau actif (en cours de saisie dans la sticky bar)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'livesession_live_roll'
        verbose_name = 'Brouillon de rouleau'
        verbose_name_plural = 'Brouillons de rouleaux'
        # Une seule session peut avoir un rouleau actif à la fois
        unique_together = [['session_key', 'is_active']]
        indexes = [
            models.Index(fields=['session_key', 'is_active']),
        ]
    
    def __str__(self):
        roll_id = self.roll_data.get('roll_id', 'Sans ID')
        status = "Actif" if self.is_active else "Archivé"
        return f"Draft rouleau: {roll_id} - {status}"


class LiveQualityControl(models.Model):
    """Brouillon des contrôles qualité - calculs des moyennes côté serveur"""
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    
    # Données des contrôles qualité en JSON
    quality_data = models.JSONField(default=dict)
    # Structure attendue:
    # {
    #     "micronnaire_left": [valeur1, valeur2, valeur3],
    #     "micronnaire_right": [valeur1, valeur2, valeur3],
    #     "micronnaire_left_avg": moyenne_calculée,
    #     "micronnaire_right_avg": moyenne_calculée,
    #     "extrait_sec": valeur,
    #     "extrait_sec_time": "HH:MM",
    #     "surface_mass_gg": valeur,
    #     "surface_mass_gc": valeur,
    #     "surface_mass_dc": valeur,
    #     "surface_mass_dd": valeur,
    #     "surface_mass_left_avg": moyenne_calculée,
    #     "surface_mass_right_avg": moyenne_calculée,
    #     "loi_given": true/false,
    #     "loi_time": "HH:MM"
    # }
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'livesession_live_quality'
        verbose_name = 'Brouillon contrôles qualité'
        verbose_name_plural = 'Brouillons contrôles qualité'
    
    def __str__(self):
        data = self.quality_data
        micronnaire_count = len([v for v in data.get('micronnaire_left', []) + data.get('micronnaire_right', []) if v])
        surface_mass_count = len([v for k, v in data.items() if k.startswith('surface_mass_') and not k.endswith('_avg') and v])
        return f"Draft qualité: {micronnaire_count} micronnaires, {surface_mass_count} masses surfaciques"