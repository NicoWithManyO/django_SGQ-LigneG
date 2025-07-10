from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from core.models import Operator


class Shift(models.Model):
    """Modèle représentant un poste de production."""
    
    VACATION_CHOICES = [
        ('Matin', 'Matin'),
        ('ApresMidi', 'Après-midi'),
        ('Nuit', 'Nuit'),
        ('Journee', 'Journée'),
    ]
    
    # Attributs principaux
    shift_id = models.CharField(max_length=50, unique=True, 
                               help_text="ID unique généré automatiquement (format: date_operator_vacation)")
    date = models.DateField(verbose_name="Date", help_text="Date de production")
    operator = models.ForeignKey(Operator, on_delete=models.CASCADE, 
                                verbose_name="Opérateur", help_text="Opérateur responsable du poste")
    vacation = models.CharField(max_length=20, choices=VACATION_CHOICES, 
                               verbose_name="Vacation", help_text="Vacation du poste")
    start_time = models.TimeField(null=True, blank=True, verbose_name="Heure de début", help_text="Heure de début du poste")
    end_time = models.TimeField(null=True, blank=True, verbose_name="Heure de fin", help_text="Heure de fin du poste")
    availability_time = models.DurationField(verbose_name="Temps disponible", help_text="Temps de disponibilité", null=True, blank=True)
    lost_time = models.DurationField(verbose_name="Temps perdu", help_text="Temps perdu", null=True, blank=True)
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
    
    @property
    def opening_time(self):
        """Calcule le temps d'ouverture à partir des heures de début et fin."""
        if not self.start_time or not self.end_time:
            return timedelta(0)
        
        # Convertir les TimeField en datetime pour le calcul
        start_datetime = datetime.combine(self.date, self.start_time)
        end_datetime = datetime.combine(self.date, self.end_time)
        
        # Si l'heure de fin est avant l'heure de début, c'est que le poste passe minuit
        if end_datetime < start_datetime:
            end_datetime += timedelta(days=1)
        
        return end_datetime - start_datetime
    
    def clean(self):
        """Validation du modèle."""
        super().clean()
        
        if self.start_time and self.end_time:
            # Vérifier que la durée du poste est raisonnable (max 24h)
            duration = self.opening_time
            if duration > timedelta(hours=24):
                raise ValidationError("La durée du poste ne peut pas dépasser 24 heures.")
            if duration <= timedelta(0):
                raise ValidationError("L'heure de fin doit être après l'heure de début.")
    
    def save(self, *args, **kwargs):
        """Génère automatiquement le shift_id et calcule les valeurs dérivées."""
        if not self.shift_id:
            # Format: JJMMAA_PrenomNom_Vacation
            date_str = self.date.strftime('%d%m%y')
            operator_clean = self.operator.full_name_no_space
            self.shift_id = f"{date_str}_{operator_clean}_{self.vacation}"
        
        # Calcul automatique des temps
        if self.start_time and self.end_time:
            # Availability_time = opening_time moins les temps d'arrêt programmés
            # Pour l'instant, on considère que availability_time = opening_time
            self.availability_time = self.opening_time
            
            # Lost_time = opening_time - availability_time
            # Pour l'instant, on calcule comme opening_time - temps de production effectif
            # (logique à adapter selon vos besoins métier)
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


class QualityControl(models.Model):
    """Modèle pour enregistrer les contrôles qualité."""
    
    # Relation avec le shift (nullable car peut ne pas encore exister)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, null=True, blank=True,
                             related_name='quality_controls',
                             verbose_name="Poste", help_text="Poste associé (si déjà sauvegardé)")
    
    # Identifiant de session pour lier au shift non sauvegardé
    session_key = models.CharField(max_length=255, help_text="Clé de session pour lier au shift en cours")
    
    # Contrôles Micronnaire
    micrometer_left_1 = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True,
                                           verbose_name="Micronnaire Gauche #1")
    micrometer_left_2 = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True,
                                           verbose_name="Micronnaire Gauche #2")
    micrometer_left_3 = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True,
                                           verbose_name="Micronnaire Gauche #3")
    micrometer_left_avg = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True,
                                             verbose_name="Micronnaire Gauche Moyenne")
    
    micrometer_right_1 = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True,
                                            verbose_name="Micronnaire Droite #1")
    micrometer_right_2 = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True,
                                            verbose_name="Micronnaire Droite #2")
    micrometer_right_3 = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True,
                                            verbose_name="Micronnaire Droite #3")
    micrometer_right_avg = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True,
                                              verbose_name="Micronnaire Droite Moyenne")
    
    # Extrait Sec
    dry_extract = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True,
                                     verbose_name="Extrait Sec (%)")
    dry_extract_time = models.TimeField(null=True, blank=True,
                                       verbose_name="Heure Extrait Sec")
    
    # Masses Surfaciques
    surface_mass_gg = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True,
                                         verbose_name="Masse Surfacique GG (g/25cm²)")
    surface_mass_gc = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True,
                                         verbose_name="Masse Surfacique GC (g/25cm²)")
    surface_mass_left_avg = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True,
                                               verbose_name="Masse Surfacique Gauche Moyenne")
    
    surface_mass_dc = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True,
                                         verbose_name="Masse Surfacique DC (g/25cm²)")
    surface_mass_dd = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True,
                                         verbose_name="Masse Surfacique DD (g/25cm²)")
    surface_mass_right_avg = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True,
                                                verbose_name="Masse Surfacique Droite Moyenne")
    
    # LOI
    loi_given = models.BooleanField(default=False, verbose_name="LOI donnée")
    loi_time = models.TimeField(null=True, blank=True, verbose_name="Heure LOI")
    
    # Validation
    is_valid = models.BooleanField(default=True, verbose_name="Contrôles valides",
                                  help_text="Indique si tous les contrôles sont dans les tolérances")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date/heure du contrôle")
    created_by = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True, blank=True,
                                  verbose_name="Contrôlé par")
    
    class Meta:
        verbose_name = "Contrôle qualité"
        verbose_name_plural = "Contrôles qualité"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        """Calcule automatiquement les moyennes avant sauvegarde."""
        # Moyenne Micronnaire Gauche
        left_values = [v for v in [self.micrometer_left_1, self.micrometer_left_2, self.micrometer_left_3] if v is not None]
        if left_values:
            self.micrometer_left_avg = sum(left_values) / len(left_values)
        
        # Moyenne Micronnaire Droite
        right_values = [v for v in [self.micrometer_right_1, self.micrometer_right_2, self.micrometer_right_3] if v is not None]
        if right_values:
            self.micrometer_right_avg = sum(right_values) / len(right_values)
        
        # Moyenne Masse Surfacique Gauche
        left_mass_values = [v for v in [self.surface_mass_gg, self.surface_mass_gc] if v is not None]
        if left_mass_values:
            self.surface_mass_left_avg = sum(left_mass_values) / len(left_mass_values)
        
        # Moyenne Masse Surfacique Droite
        right_mass_values = [v for v in [self.surface_mass_dc, self.surface_mass_dd] if v is not None]
        if right_mass_values:
            self.surface_mass_right_avg = sum(right_mass_values) / len(right_mass_values)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.shift:
            return f"Contrôles {self.shift.shift_id} - {self.created_at.strftime('%H:%M')}"
        return f"Contrôles session {self.session_key} - {self.created_at.strftime('%H:%M')}"


class Roll(models.Model):
    """Modèle représentant un rouleau de production."""
    
    # Identifiant unique du rouleau
    roll_id = models.CharField(max_length=50, unique=True, 
                              help_text="ID unique du rouleau (format: OF_NumRouleau)")
    
    # Relation avec le shift (nullable car peut être créé avant le shift)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, 
                             related_name='rolls',
                             verbose_name="Poste de production",
                             null=True, blank=True,
                             help_text="Poste associé (sera lié lors de la sauvegarde du poste)")
    
    # Identifiant de session pour lier au shift non sauvegardé
    session_key = models.CharField(max_length=255, null=True, blank=True,
                                  help_text="Clé de session pour lier au shift en cours")
    
    # Relation avec l'ordre de fabrication
    fabrication_order = models.ForeignKey('core.FabricationOrder', on_delete=models.CASCADE,
                                         related_name='rolls',
                                         verbose_name="Ordre de fabrication",
                                         null=True, blank=True)
    
    # Données de production
    roll_number = models.PositiveIntegerField(verbose_name="N° Rouleau")
    length = models.DecimalField(max_digits=10, decimal_places=2, 
                                verbose_name="Longueur (m)")
    tube_mass = models.DecimalField(max_digits=10, decimal_places=2, 
                                   verbose_name="Masse tube (kg)")
    total_mass = models.DecimalField(max_digits=10, decimal_places=2, 
                                    verbose_name="Masse totale (kg)")
    
    # Statut et destination
    STATUS_CHOICES = [
        ('CONFORME', 'Conforme'),
        ('NON_CONFORME', 'Non conforme'),
    ]
    
    DESTINATION_CHOICES = [
        ('PRODUCTION', 'Production'),
        ('DECOUPE', 'Découpe'),
        ('DECHETS', 'Déchets'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
                             default='CONFORME', verbose_name="Statut")
    destination = models.CharField(max_length=20, choices=DESTINATION_CHOICES,
                                  default='PRODUCTION', verbose_name="Destination")
    
    # Détails de conformité
    has_blocking_defects = models.BooleanField(default=False, 
                                              verbose_name="Défauts bloquants")
    has_thickness_issues = models.BooleanField(default=False, 
                                              verbose_name="Problèmes d'épaisseur")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Rouleau"
        verbose_name_plural = "Rouleaux"
        ordering = ['shift', 'roll_number']
        unique_together = [['shift', 'roll_number']]
    
    def save(self, *args, **kwargs):
        """Génère automatiquement le roll_id selon le statut."""
        if not self.roll_id:
            if self.status == 'NON_CONFORME':
                # Format pour non conforme: OFDecoupe_JJMMAA_HHMM
                from datetime import datetime
                now = datetime.now()
                date_str = now.strftime('%d%m%y')
                time_str = now.strftime('%H%M')
                self.roll_id = f"OFDecoupe_{date_str}_{time_str}"
            elif self.fabrication_order and self.roll_number:
                # Format pour conforme: OF_NumRouleau (ex: OF123_001)
                self.roll_id = f"{self.fabrication_order.order_number}_{self.roll_number:03d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.roll_id} - {self.length}m"


class RollDefect(models.Model):
    """Défauts constatés sur les rouleaux."""
    
    POSITION_SIDE_CHOICES = [
        ('left', 'Gauche'),
        ('center', 'Centre'), 
        ('right', 'Droite'),
    ]
    
    # Relation avec le rouleau
    roll = models.ForeignKey(Roll, on_delete=models.CASCADE, 
                            related_name='defects',
                            verbose_name="Rouleau")
    
    # Type de défaut (pour l'instant simple CharField, à terme ForeignKey vers DefectType)
    defect_name = models.CharField(max_length=100, verbose_name="Nom du défaut")
    
    # Position sur le rouleau
    meter_position = models.PositiveIntegerField(verbose_name="Position (mètre)")
    side_position = models.CharField(max_length=10, choices=POSITION_SIDE_CHOICES,
                                   verbose_name="Côté")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Défaut rouleau"
        verbose_name_plural = "Défauts rouleaux" 
        ordering = ['roll', 'meter_position']
        unique_together = [['roll', 'meter_position', 'side_position', 'defect_name']]
    
    def __str__(self):
        return f"{self.roll.roll_id} - {self.defect_name} à {self.meter_position}m ({self.get_side_position_display()})"


class RollThickness(models.Model):
    """Mesures d'épaisseur sur les rouleaux."""
    
    MEASUREMENT_POINTS = [
        ('GG', 'Gauche Gauche'),
        ('GC', 'Gauche Centre'), 
        ('GD', 'Gauche Droite'),
        ('DG', 'Droite Gauche'),
        ('DC', 'Droite Centre'),
        ('DD', 'Droite Droite'),
    ]
    
    # Relation avec le rouleau
    roll = models.ForeignKey(Roll, on_delete=models.CASCADE, 
                            related_name='thickness_measurements',
                            verbose_name="Rouleau")
    
    # Position de mesure
    meter_position = models.PositiveIntegerField(verbose_name="Position (mètre)")
    measurement_point = models.CharField(max_length=2, choices=MEASUREMENT_POINTS,
                                       verbose_name="Point de mesure")
    
    # Valeur mesurée
    thickness_value = models.DecimalField(max_digits=5, decimal_places=2,
                                        verbose_name="Épaisseur (mm)")
    
    # Indique si c'est une mesure de rattrapage
    is_catchup = models.BooleanField(default=False, verbose_name="Mesure de rattrapage")
    
    # Validation (sera calculée selon les spécifications)
    is_within_tolerance = models.BooleanField(default=True, verbose_name="Dans les tolérances")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Mesure d'épaisseur"
        verbose_name_plural = "Mesures d'épaisseur"
        ordering = ['roll', 'meter_position', 'measurement_point']
        # Pas d'unique_together car on peut avoir plusieurs mesures (normale + rattrapage)
    
    def __str__(self):
        catchup_str = " (rattrapage)" if self.is_catchup else ""
        return f"{self.roll.roll_id} - {self.measurement_point} à {self.meter_position}m: {self.thickness_value}mm{catchup_str}"
