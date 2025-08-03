from django.db import models


class Shift(models.Model):
    """Modèle représentant un poste de production."""
    
    VACATION_CHOICES = [
        ('Matin', 'Matin'),
        ('ApresMidi', 'Après-midi'),
        ('Nuit', 'Nuit'),
        ('Journee', 'Journée'),
    ]
    
    # Identifiant unique
    shift_id = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name="ID du poste",
        help_text="Format: JJMMAA_PrenomNom_Vacation"
    )
    
    # Informations principales
    date = models.DateField(
        verbose_name="Date",
        help_text="Date du poste de production"
    )
    
    operator = models.ForeignKey(
        'planification.Operator',
        on_delete=models.SET_NULL,
        null=True,
        related_name='shifts',
        verbose_name="Opérateur",
        help_text="Opérateur responsable du poste"
    )
    
    vacation = models.CharField(
        max_length=20,
        choices=VACATION_CHOICES,
        verbose_name="Vacation",
        help_text="Période de travail"
    )
    
    # Horaires
    start_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Heure de début",
        help_text="Heure de début du poste"
    )
    
    end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Heure de fin",
        help_text="Heure de fin du poste"
    )
    
    # Temps de production
    availability_time = models.DurationField(
        null=True,
        blank=True,
        verbose_name="Temps disponible",
        help_text="Temps de disponibilité = Temps d'ouverture - Temps perdu"
    )
    
    lost_time = models.DurationField(
        null=True,
        blank=True,
        verbose_name="Temps perdu",
        help_text="Somme des temps d'arrêt"
    )
    
    # Les champs de production ont été déplacés vers le modèle TRS
    # et sont maintenant accessibles via les propriétés @property
    
    # Moyennes du poste
    avg_thickness_left_shift = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Épaisseur moyenne gauche (mm)",
        help_text="Moyenne des épaisseurs gauches de tous les rouleaux"
    )
    
    avg_thickness_right_shift = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Épaisseur moyenne droite (mm)",
        help_text="Moyenne des épaisseurs droites de tous les rouleaux"
    )
    
    avg_grammage_shift = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name="Grammage moyen (g/m)",
        help_text="Moyenne des grammages de tous les rouleaux"
    )
    
    # État machine
    started_at_beginning = models.BooleanField(
        default=False,
        verbose_name="Machine démarrée en début",
        help_text="Machine démarrée en début de poste"
    )
    
    meter_reading_start = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Métrage début (m)",
        help_text="Relevé compteur en début de poste"
    )
    
    started_at_end = models.BooleanField(
        default=False,
        verbose_name="Machine démarrée en fin",
        help_text="Machine démarrée en fin de poste"
    )
    
    meter_reading_end = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Métrage fin (m)",
        help_text="Relevé compteur en fin de poste"
    )
    
    # Check-list
    checklist_signed = models.CharField(
        max_length=5,
        null=True,
        blank=True,
        verbose_name="Signature check-list",
        help_text="Initiales de l'opérateur"
    )
    
    checklist_signed_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Heure signature check-list"
    )
    
    # Commentaires
    operator_comments = models.TextField(
        blank=True,
        verbose_name="Commentaires opérateur",
        help_text="Observations de l'opérateur"
    )
    
    # Champ temporaire pour compatibilité avec la base de données
    wound_length_end = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=0,
        verbose_name="Longueur enroulée fin (temporaire)"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Poste"
        verbose_name_plural = "Postes"
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['-date', 'vacation']),
            models.Index(fields=['operator', '-date']),
        ]
    
    def __str__(self):
        return self.shift_id
    
    def save(self, *args, **kwargs):
        """Génère automatiquement le shift_id si non fourni et gère les contraintes métier."""
        # Générer le shift_id si non fourni
        if not self.shift_id:
            date_str = self.date.strftime('%d%m%y')
            if self.operator:
                operator_clean = f"{self.operator.first_name}{self.operator.last_name}".replace(' ', '')
            else:
                operator_clean = "SansOperateur"
            self.shift_id = f"{date_str}_{operator_clean}_{self.vacation}"
        
        # Si machine pas démarrée en début, effacer le métrage début
        if not self.started_at_beginning:
            self.meter_reading_start = None
        
        # Si machine pas démarrée en fin, effacer le métrage fin
        if not self.started_at_end:
            self.meter_reading_end = None
        
        super().save(*args, **kwargs)
    
    # === PROPRIÉTÉS POUR ACCÉDER AUX DONNÉES TRS ===
    @property
    def total_length(self):
        """Longueur totale produite (depuis TRS)."""
        if hasattr(self, 'trs'):
            return self.trs.total_length
        return 0
    
    @property
    def ok_length(self):
        """Longueur conforme (depuis TRS)."""
        if hasattr(self, 'trs'):
            return self.trs.ok_length
        return 0
    
    @property
    def nok_length(self):
        """Longueur non conforme (depuis TRS)."""
        if hasattr(self, 'trs'):
            return self.trs.nok_length
        return 0
    
    @property
    def raw_waste_length(self):
        """Déchet brut (depuis TRS)."""
        if hasattr(self, 'trs'):
            return self.trs.raw_waste_length
        return 0