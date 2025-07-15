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
    operator = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True,
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
    
    # Moyennes des rouleaux du poste
    avg_thickness_left_shift = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                                  verbose_name="Moyenne épaisseur gauche",
                                                  help_text="Moyenne des moyennes gauches de tous les rouleaux")
    avg_thickness_right_shift = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                                   verbose_name="Moyenne épaisseur droite", 
                                                   help_text="Moyenne des moyennes droites de tous les rouleaux")
    avg_grammage_shift = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True,
                                            verbose_name="Grammage moyen",
                                            help_text="Moyenne des grammages de tous les rouleaux (g/m)")
    
    # Attributs techniques - Début de poste
    started_at_beginning = models.BooleanField(default=False, verbose_name="Machine démarrée", help_text="Machine démarrée en début de poste")
    meter_reading_start = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                            verbose_name="Lg enroulée (m)", help_text="Métrage en début de poste (si démarrée)")
    
    # Attributs techniques - Fin de poste  
    started_at_end = models.BooleanField(default=False, verbose_name="Machine démarrée", help_text="Machine démarrée en fin de poste")
    meter_reading_end = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                          verbose_name="Lg enroulée (m)", help_text="Métrage en fin de poste (si démarrée)")
    
    # Check-list
    checklist_signed = models.CharField(max_length=5, null=True, blank=True, 
                                      verbose_name="Signature check-list", help_text="Initiales de l'opérateur")
    checklist_signed_time = models.TimeField(null=True, blank=True,
                                           verbose_name="Heure signature check-list")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Poste"
        verbose_name_plural = "Postes"
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return self.shift_id
    
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
    
    @property
    def trs(self):
        """Calcule le TRS (Taux de Rendement Synthétique) = (Longueur OK / Longueur Totale) * 100."""
        if self.total_length and self.total_length > 0:
            return round((self.ok_length / self.total_length) * 100, 1)
        return 0
    
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
    
    def calculate_lost_time(self):
        """Calcule le temps perdu total à partir des entrées de temps d'arrêt."""
        from django.db.models import Sum
        total_minutes = self.lost_time_entries.aggregate(
            total=Sum('duration')
        )['total'] or 0
        return timedelta(minutes=total_minutes)
    
    def calculate_roll_averages(self):
        """Calcule les moyennes d'épaisseur et de grammage de tous les rouleaux du poste."""
        from django.db.models import Avg
        
        # Récupérer uniquement les rouleaux avec des données d'épaisseur
        rolls_with_thickness = self.rolls.exclude(
            avg_thickness_left__isnull=True,
            avg_thickness_right__isnull=True
        )
        
        if rolls_with_thickness.exists():
            # Moyenne des moyennes gauches
            avg_left = rolls_with_thickness.aggregate(
                avg=Avg('avg_thickness_left')
            )['avg']
            if avg_left is not None:
                self.avg_thickness_left_shift = round(avg_left, 2)
            
            # Moyenne des moyennes droites
            avg_right = rolls_with_thickness.aggregate(
                avg=Avg('avg_thickness_right')
            )['avg']
            if avg_right is not None:
                self.avg_thickness_right_shift = round(avg_right, 2)
        
        # Moyenne des grammages (pour tous les rouleaux avec masse et longueur)
        rolls_with_grammage = []
        for roll in self.rolls.all():
            if roll.net_mass and roll.length and roll.length > 0:
                rolls_with_grammage.append(roll.grammage)
        
        if rolls_with_grammage:
            self.avg_grammage_shift = round(sum(rolls_with_grammage) / len(rolls_with_grammage), 1)
    
    def save(self, *args, **kwargs):
        """Génère automatiquement le shift_id et calcule les valeurs dérivées."""
        if not self.shift_id:
            # Format: JJMMAA_PrenomNom_Vacation
            date_str = self.date.strftime('%d%m%y')
            if self.operator:
                operator_clean = self.operator.full_name_no_space
            else:
                operator_clean = "SansOperateur"
            self.shift_id = f"{date_str}_{operator_clean}_{self.vacation}"
        
        # Calcul automatique des temps
        if self.start_time and self.end_time:
            # Lost_time = somme de tous les temps d'arrêt déclarés
            # Si l'objet n'a pas encore de pk, on ne peut pas calculer (pas encore de relations)
            if self.pk:
                self.lost_time = self.calculate_lost_time()
            else:
                self.lost_time = timedelta(seconds=0)
            
            # Availability_time (Temps Disponible) = opening_time (Temps d'Ouverture) - lost_time (Temps Perdu)
            self.availability_time = self.opening_time - self.lost_time
        
        # Calcul automatique du déchet brut
        if self.total_length and self.ok_length and self.nok_length:
            self.raw_waste_length = self.total_length - (self.ok_length + self.nok_length)
        else:
            self.raw_waste_length = 0
        
        # D'abord sauvegarder pour avoir un ID
        super().save(*args, **kwargs)
        
        # Calculer les moyennes des rouleaux si on a un ID
        if self.pk:
            self.calculate_roll_averages()
            # Sauvegarder à nouveau si les moyennes ont changé
            if 'update_fields' not in kwargs:
                super().save(update_fields=['avg_thickness_left_shift', 'avg_thickness_right_shift', 'avg_grammage_shift'])


class LostTimeEntry(models.Model):
    """Modèle pour enregistrer les temps d'arrêt."""
    
    # Relation avec le shift (nullable car peut ne pas encore exister)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, null=True, blank=True,
                             related_name='lost_time_entries',
                             verbose_name="Poste", help_text="Poste associé (si déjà sauvegardé)")
    
    # Identifiant de session pour lier au shift non sauvegardé
    session_key = models.CharField(max_length=255, null=True, blank=True,
                                  help_text="Clé de session pour lier au shift en cours")
    
    # Données du temps d'arrêt
    motif = models.CharField(max_length=100, verbose_name="Motif d'arrêt")
    comment = models.TextField(blank=True, verbose_name="Commentaire")
    duration = models.PositiveIntegerField(verbose_name="Durée (minutes)", 
                                          help_text="Durée de l'arrêt en minutes")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Temps d'arrêt"
        verbose_name_plural = "Temps d'arrêt"
        ordering = ['-created_at', '-id']
    
    def __str__(self):
        if self.shift:
            return f"{self.shift.shift_id} - {self.motif} ({self.duration}min)"
        return f"Session {self.session_key} - {self.motif} ({self.duration}min)"


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
        ordering = ['-created_at', '-id']
    
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
    # SET_NULL pour garder les rouleaux même si le poste est supprimé
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, 
                             related_name='rolls',
                             verbose_name="Poste de production",
                             null=True, blank=True,
                             help_text="Poste associé (sera lié lors de la sauvegarde du poste)")
    
    # ID du shift stocké en texte pour traçabilité (garde l'ID même si le shift est supprimé)
    shift_id_str = models.CharField(max_length=50, null=True, blank=True,
                                   verbose_name="ID du poste (texte)",
                                   help_text="ID du poste conservé même après suppression")
    
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
                                   verbose_name="Masse tube (g)")
    total_mass = models.DecimalField(max_digits=10, decimal_places=2, 
                                    verbose_name="Masse totale (g)")
    
    # Statut et destination
    STATUS_CHOICES = [
        ('CONFORME', 'Conforme'),
        ('NON_CONFORME', 'Non conforme'),
    ]
    
    DESTINATION_CHOICES = [
        ('PRODUCTION', 'Production'),
        ('DECOUPE', 'Découpe'),
        ('DECOUPE_FORCEE', 'Découpe Forcée'),
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
    
    # Moyennes d'épaisseurs
    avg_thickness_left = models.DecimalField(max_digits=5, decimal_places=2, 
                                           null=True, blank=True,
                                           verbose_name="Épaisseur moyenne gauche (mm)")
    avg_thickness_right = models.DecimalField(max_digits=5, decimal_places=2, 
                                            null=True, blank=True,
                                            verbose_name="Épaisseur moyenne droite (mm)")
    
    # Grammage calculé lors de la sauvegarde
    grammage_calc = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True,
                                       verbose_name="Grammage calculé",
                                       help_text="Grammage calculé et sauvegardé (g/m)")
    
    # Masse nette calculée
    net_mass = models.DecimalField(max_digits=10, decimal_places=2, 
                                  null=True, blank=True,
                                  verbose_name="Masse nette (g)",
                                  help_text="Masse totale - Masse tube")
    
    # Commentaire
    comment = models.TextField(blank=True, null=True,
                             verbose_name="Commentaire",
                             help_text="Commentaire libre sur le rouleau")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Rouleau"
        verbose_name_plural = "Rouleaux"
        ordering = ['-created_at', '-id']
        unique_together = [['shift', 'roll_number']]
    
    def calculate_thickness_averages(self):
        """Calcule les moyennes d'épaisseur gauche et droite à partir des mesures."""
        from django.db.models import Avg
        
        # Points de mesure gauche: GG, GC, GD
        left_points = ['GG', 'GC', 'GD'] 
        # Points de mesure droite: DG, DC, DD
        right_points = ['DG', 'DC', 'DD']
        
        # Calculer moyenne gauche
        left_avg = self.thickness_measurements.filter(
            measurement_point__in=left_points,
            is_catchup=False  # Ne prendre que les mesures normales
        ).aggregate(avg=Avg('thickness_value'))['avg']
        
        # Calculer moyenne droite
        right_avg = self.thickness_measurements.filter(
            measurement_point__in=right_points,
            is_catchup=False
        ).aggregate(avg=Avg('thickness_value'))['avg']
        
        if left_avg:
            self.avg_thickness_left = round(left_avg, 2)
        if right_avg:
            self.avg_thickness_right = round(right_avg, 2)
    
    @property
    def grammage(self):
        """Calcule le grammage (g/m) du rouleau."""
        if self.net_mass and self.length and self.length > 0:
            # net_mass est en grammes, length en mètres
            # donc net_mass / length donne des g/m
            return round(float(self.net_mass) / float(self.length), 1)
        return 0
    
    def save(self, *args, **kwargs):
        """Génère automatiquement le roll_id selon le statut si non fourni et calcule la masse nette."""
        if not self.roll_id:
            # Génération de secours si l'ID n'est pas fourni par la vue
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
        
        # Calculer la masse nette
        if self.total_mass and self.tube_mass:
            self.net_mass = self.total_mass - self.tube_mass
        
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


class MachineParameters(models.Model):
    """Paramètres machine pour la production."""
    
    # Identification du profil
    name = models.CharField(max_length=100, unique=True, 
                           verbose_name="Nom du profil",
                           help_text="Nom ou profil des paramètres machine")
    
    # Paramètres FIBRAGE
    oxygen_primary = models.DecimalField(max_digits=6, decimal_places=2, 
                                       null=True, blank=True,
                                       verbose_name="Oxygène primaire",
                                       help_text="Débit oxygène primaire")
    oxygen_secondary = models.DecimalField(max_digits=6, decimal_places=2,
                                         null=True, blank=True,
                                         verbose_name="Oxygène secondaire", 
                                         help_text="Débit oxygène secondaire")
    propane_primary = models.DecimalField(max_digits=6, decimal_places=2,
                                        null=True, blank=True,
                                        verbose_name="Propane primaire",
                                        help_text="Débit propane primaire")
    propane_secondary = models.DecimalField(max_digits=6, decimal_places=2,
                                          null=True, blank=True,
                                          verbose_name="Propane secondaire",
                                          help_text="Débit propane secondaire")
    speed_primary = models.DecimalField(max_digits=6, decimal_places=2,
                                      null=True, blank=True,
                                      verbose_name="Vitesse primaire",
                                      help_text="Vitesse primaire")
    speed_secondary = models.DecimalField(max_digits=6, decimal_places=2,
                                        null=True, blank=True,
                                        verbose_name="Vitesse secondaire",
                                        help_text="Vitesse secondaire")
    
    # Paramètres ENSIMEUSE
    belt_speed = models.DecimalField(max_digits=6, decimal_places=2,
                                   null=True, blank=True,
                                   verbose_name="Vitesse tapis",
                                   help_text="Vitesse du tapis en m/h")
    
    # Métadonnées
    is_active = models.BooleanField(default=True,
                                  verbose_name="Actif",
                                  help_text="Profil actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Paramètres machine"
        verbose_name_plural = "Paramètres machine"
        ordering = ['name']
    
    def __str__(self):
        return f"Profil: {self.name}"
    
    @property
    def belt_speed_m_per_minute(self):
        """Retourne la vitesse du tapis en m/min (conversion depuis m/h)."""
        if self.belt_speed:
            return round(float(self.belt_speed) / 60, 2)
        return None
