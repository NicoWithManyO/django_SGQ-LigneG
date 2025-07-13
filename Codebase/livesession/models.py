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
        operator = self.shift_data.get('operator_name', 'Sans opérateur')
        date = self.shift_data.get('date', 'Sans date')
        return f"Draft: {operator} - {date}"