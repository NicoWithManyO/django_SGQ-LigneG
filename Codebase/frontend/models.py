from django.db import models
from django.utils import timezone
from datetime import timedelta

class ProductionDraft(models.Model):
    """
    Modèle pour stocker l'état brouillon de la production
    Un draft par session utilisateur
    """
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    
    # État séparé par section pour granularité
    shift_data = models.JSONField(default=dict)
    quality_data = models.JSONField(default=dict)
    checklist_data = models.JSONField(default=dict)
    rolls_data = models.JSONField(default=dict)
    lost_time_data = models.JSONField(default=dict)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Brouillon de production"
        verbose_name_plural = "Brouillons de production"
        
    def __str__(self):
        return f"Draft {self.session_key[:8]} - {self.updated_at.strftime('%d/%m %H:%M')}"
    
    def update_section(self, section, data):
        """Met à jour une section spécifique du draft"""
        if hasattr(self, f"{section}_data"):
            setattr(self, f"{section}_data", data)
            self.save(update_fields=[f"{section}_data", "updated_at"])
    
    def clear_after_shift_save(self):
        """
        Nettoie le draft après sauvegarde d'un poste
        Garde certaines données pour le poste suivant
        """
        # Garder certains champs du shift
        preserved_shift = {
            'operator': self.shift_data.get('operator'),
            'started_at_end': self.shift_data.get('started_at_end', True),
            'meter_reading_start': self.shift_data.get('meter_reading_end', ''),
            'meter_reading_end': '',
            # Les OF et longueurs cibles
            'fabrication_order': self.shift_data.get('fabrication_order'),
            'cutting_order': self.shift_data.get('cutting_order'),
            'target_length': self.shift_data.get('target_length'),
        }
        
        # Vider les sections
        self.shift_data = preserved_shift
        self.quality_data = {}
        self.checklist_data = {}
        self.lost_time_data = {'entries': [], 'total_minutes': 0}
        
        # Garder le rouleau en cours si non sauvé
        if self.rolls_data.get('current', {}).get('status') == 'draft':
            # Garder le rouleau actuel
            pass
        else:
            # Sinon réinitialiser
            self.rolls_data = {'current': {}, 'saved': []}
        
        self.save()
    
    @classmethod
    def cleanup_old_drafts(cls, days=7):
        """Supprime les drafts non modifiés depuis X jours"""
        cutoff = timezone.now() - timedelta(days=days)
        cls.objects.filter(updated_at__lt=cutoff).delete()