from django.db import models
from core.models import Operator


class Shift(models.Model):
    """Modèle représentant un poste de production."""
    
    VACATION_CHOICES = [
        ('Matin', 'Matin'),
        ('ApresMidi', 'Après-midi'),
        ('Nuit', 'Nuit'),
    ]
    
    # Attributs principaux
    shift_id = models.CharField(max_length=50, unique=True, 
                               help_text="ID unique généré automatiquement (format: date_operator_vacation)")
    date = models.DateField(verbose_name="Date", help_text="Date de production")
    operator = models.ForeignKey(Operator, on_delete=models.CASCADE, 
                                verbose_name="Opérateur", help_text="Opérateur responsable du poste")
    vacation = models.CharField(max_length=20, choices=VACATION_CHOICES, 
                               verbose_name="Vacation", help_text="Vacation du poste")
    opening_time = models.DurationField(verbose_name="Temps d'ouverture", help_text="Temps d'ouverture du poste")
    availability_time = models.DurationField(verbose_name="Temps disponible", help_text="Temps de disponibilité")
    lost_time = models.DurationField(verbose_name="Temps perdu", help_text="Temps perdu")
    operator_comments = models.TextField(blank=True, 
                                       verbose_name="", help_text="Commentaires de l'opérateur")
    
    # Attributs longueurs
    total_length = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                     help_text="Longueur totale en mètres")
    ok_length = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                  help_text="Longueur conforme en mètres")
    nok_length = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                   help_text="Longueur non conforme en mètres")
    raw_waste_length = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                         help_text="Longueur déchet brut en mètres")
    
    # Attributs techniques - Début de poste
    started_at_beginning = models.BooleanField(default=False, verbose_name="Machine démarrée", help_text="Machine démarrée en début de poste")
    meter_reading_start = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                            verbose_name="Lg enroulée (m)", help_text="Métrage en début de poste (si démarrée)")
    
    # Attributs techniques - Fin de poste  
    started_at_end = models.BooleanField(default=False, verbose_name="Machine démarrée", help_text="Machine démarrée en fin de poste")
    meter_reading_end = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                          verbose_name="Lg enroulée (m)", help_text="Métrage en fin de poste (si démarrée)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Poste"
        verbose_name_plural = "Postes"
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.shift_id} - {self.operator.full_name} ({self.vacation})"
    
    def save(self, *args, **kwargs):
        """Génère automatiquement le shift_id et calcule les valeurs dérivées."""
        if not self.shift_id:
            # Format: JJMMAA_PrenomNom_Vacation
            date_str = self.date.strftime('%d%m%y')
            operator_clean = self.operator.full_name_no_space
            self.shift_id = f"{date_str}_{operator_clean}_{self.vacation}"
        
        # Calcul automatique des temps
        if self.opening_time:
            # Availability_time = opening_time moins les temps d'arrêt programmés
            # Pour l'instant, on considère que availability_time = opening_time
            self.availability_time = self.opening_time
            
            # Lost_time = opening_time - availability_time
            # Pour l'instant, on calcule comme opening_time - temps de production effectif
            # (logique à adapter selon vos besoins métier)
            from datetime import timedelta
            self.lost_time = timedelta(seconds=0)  # À calculer selon votre logique
        
        # Calcul automatique du déchet brut
        if self.total_length and self.ok_length and self.nok_length:
            self.raw_waste_length = self.total_length - (self.ok_length + self.nok_length)
        else:
            self.raw_waste_length = 0
            
        super().save(*args, **kwargs)


class CurrentProd(models.Model):
    """Modèle pour sauvegarder automatiquement les données en cours de saisie."""
    
    # Identifiant de session/utilisateur (pour différencier les saisies)
    session_key = models.CharField(max_length=255, help_text="Clé de session pour identifier la saisie")
    
    # Données du formulaire sérialisées
    form_data = models.JSONField(default=dict, help_text="Données du formulaire en JSON")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Production en cours"
        verbose_name_plural = "Productions en cours"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Saisie {self.session_key} - {self.updated_at.strftime('%H:%M:%S')}"
