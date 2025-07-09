from django.db import models
from django.core.exceptions import ValidationError


class DefectType(models.Model):
    """Types de défauts avec leur criticité."""
    
    SEVERITY_CHOICES = [
        ('non_blocking', 'Non bloquant'),
        ('blocking', 'Bloquant'),
        ('threshold', 'Bloquant selon seuil'),
    ]
    
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom du défaut")
    description = models.TextField(blank=True, verbose_name="Description")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, verbose_name="Criticité")
    threshold_value = models.PositiveIntegerField(
        null=True, blank=True, 
        verbose_name="Seuil de tolérance",
        help_text="Nombre maximum autorisé (pour les défauts à seuil)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Type de défaut"
        verbose_name_plural = "Types de défauts"
        ordering = ['name']
    
    def clean(self):
        """Validation métier."""
        if self.severity == 'threshold' and not self.threshold_value:
            raise ValidationError({
                'threshold_value': 'Un seuil de tolérance est requis pour les défauts à seuil'
            })
    
    def __str__(self):
        return f"{self.name} ({self.get_severity_display()})"


class RollDefect(models.Model):
    """Défauts constatés sur les rouleaux."""
    
    POSITION_SIDE_CHOICES = [
        ('left', 'Gauche'),
        ('center', 'Centre'), 
        ('right', 'Droite'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('resolved', 'Résolu'),
        ('blocking', 'Bloquant'),
    ]
    
    # Identification du rouleau (pour l'instant string, plus tard FK vers Roll)
    roll_id = models.CharField(max_length=50, verbose_name="ID Rouleau", 
                              help_text="Format: OF_NumRouleau")
    
    # Défaut
    defect_type = models.ForeignKey(DefectType, on_delete=models.CASCADE, 
                                   verbose_name="Type de défaut")
    description = models.TextField(verbose_name="Description du défaut")
    
    # Position sur le rouleau
    meter_position = models.PositiveIntegerField(verbose_name="Position (mètre)")
    side_position = models.CharField(max_length=10, choices=POSITION_SIDE_CHOICES,
                                   verbose_name="Côté")
    
    # Statut et gravité
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
                            default='pending', verbose_name="Statut")
    is_blocking = models.BooleanField(default=False, verbose_name="Bloquant")
    
    # Métadonnées
    detected_at = models.DateTimeField(auto_now_add=True, verbose_name="Détecté le")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Résolu le")
    operator_comments = models.TextField(blank=True, verbose_name="Commentaires opérateur")
    
    class Meta:
        verbose_name = "Défaut rouleau"
        verbose_name_plural = "Défauts rouleaux" 
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['roll_id']),
            models.Index(fields=['meter_position']),
            models.Index(fields=['status']),
        ]
    
    def save(self, *args, **kwargs):
        """Auto-déterminer si le défaut est bloquant."""
        if self.defect_type.severity == 'blocking':
            self.is_blocking = True
            self.status = 'blocking'
        elif self.defect_type.severity == 'threshold':
            # Compter les défauts du même type sur ce rouleau
            count = RollDefect.objects.filter(
                roll_id=self.roll_id,
                defect_type=self.defect_type
            ).exclude(pk=self.pk).count()
            
            if count >= self.defect_type.threshold_value:
                self.is_blocking = True
                self.status = 'blocking'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.roll_id} - {self.defect_type.name} à {self.meter_position}m"


class ThicknessMeasurement(models.Model):
    """Mesures d'épaisseur sur les rouleaux."""
    
    MEASUREMENT_POINTS = [
        ('G1', 'Gauche 1'),
        ('G2', 'Gauche 2'), 
        ('G3', 'Gauche 3'),
        ('D1', 'Droite 1'),
        ('D2', 'Droite 2'),
        ('D3', 'Droite 3'),
    ]
    
    # Identification du rouleau (pour l'instant string, plus tard FK vers Roll)
    roll_id = models.CharField(max_length=50, verbose_name="ID Rouleau",
                              help_text="Format: OF_NumRouleau")
    
    # Position de mesure
    meter_position = models.PositiveIntegerField(verbose_name="Position (mètre)")
    measurement_point = models.CharField(max_length=2, choices=MEASUREMENT_POINTS,
                                       verbose_name="Point de mesure")
    
    # Valeur mesurée
    thickness_value = models.DecimalField(max_digits=5, decimal_places=2,
                                        verbose_name="Épaisseur (mm)")
    
    # Validation qualité
    is_within_tolerance = models.BooleanField(default=True, verbose_name="Dans les tolérances")
    min_tolerance = models.DecimalField(max_digits=5, decimal_places=2, default=4.0,
                                      verbose_name="Tolérance min (mm)")
    max_tolerance = models.DecimalField(max_digits=5, decimal_places=2, default=8.0,
                                      verbose_name="Tolérance max (mm)")
    
    # Métadonnées
    measured_at = models.DateTimeField(auto_now_add=True, verbose_name="Mesuré le")
    operator_comments = models.TextField(blank=True, verbose_name="Commentaires")
    
    class Meta:
        verbose_name = "Mesure d'épaisseur"
        verbose_name_plural = "Mesures d'épaisseur"
        ordering = ['roll_id', 'meter_position', 'measurement_point']
        unique_together = ['roll_id', 'meter_position', 'measurement_point']
        indexes = [
            models.Index(fields=['roll_id']),
            models.Index(fields=['meter_position']),
            models.Index(fields=['is_within_tolerance']),
        ]
    
    def clean(self):
        """Validation des valeurs."""
        if self.min_tolerance >= self.max_tolerance:
            raise ValidationError({
                'max_tolerance': 'La tolérance max doit être supérieure à la tolérance min'
            })
    
    def save(self, *args, **kwargs):
        """Auto-validation des tolérances."""
        self.is_within_tolerance = (
            self.min_tolerance <= self.thickness_value <= self.max_tolerance
        )
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.roll_id} - {self.measurement_point} à {self.meter_position}m: {self.thickness_value}mm"



class Specification(models.Model):
    """Spécifications générales pour tous types de contrôles qualité."""
    
    SPEC_TYPES = [
        ('thickness', 'Épaisseur'),
        ('micrometer', 'Micronnaire'),
        ('surface_mass', 'Masse surfacique'),
        ('dry_extract', 'Extrait sec'),
    ]
    
    # Type de spécification
    spec_type = models.CharField(max_length=20, choices=SPEC_TYPES, verbose_name="Type")
    
    # Nom/Produit de la spécification
    name = models.CharField(max_length=50, verbose_name="Nom",
                          help_text="Ex: 80gr/m², 40gr/m²")
    
    # Valeurs de spécification (toutes optionnelles)
    value_min = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True,
                                   verbose_name="Valeur minimale",
                                   help_text="Seuil minimum critique")
    value_min_alert = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True,
                                         verbose_name="Valeur minimale alerte",
                                         help_text="Seuil d'alerte minimum")
    value_nominal = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True,
                                       verbose_name="Valeur nominale",
                                       help_text="Valeur cible standard")
    value_max_alert = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True,
                                         verbose_name="Valeur maximale alerte",
                                         help_text="Seuil d'alerte maximum")
    value_max = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True,
                                   verbose_name="Valeur maximale",
                                   help_text="Seuil maximum critique")
    
    # Unité de mesure
    unit = models.CharField(max_length=10, blank=True, verbose_name="Unité",
                          help_text="Ex: mm, %, g/m²")
    
    # Nombre maximum de valeurs NOK autorisées (pour les épaisseurs)
    max_nok = models.PositiveIntegerField(null=True, blank=True, verbose_name="Max NOK",
                                         help_text="Nombre maximum de mesures NOK autorisées")
    
    # Indique si le non-respect de cette spec est bloquant
    is_blocking = models.BooleanField(default=True, verbose_name="Bloquant",
                                     help_text="Le non-respect de cette spec rend le produit non conforme")
    
    # Métadonnées
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    comments = models.TextField(blank=True, verbose_name="Commentaires")
    
    class Meta:
        verbose_name = "Spécification"
        verbose_name_plural = "Spécifications"
        ordering = ['spec_type', 'name']
        unique_together = [['spec_type', 'name']]
        indexes = [
            models.Index(fields=['spec_type', 'is_active']),
        ]
    
    def clean(self):
        """Validation des valeurs."""
        # Vérifier la cohérence des valeurs si elles sont définies
        values = [v for v in [self.value_min, self.value_min_alert, self.value_nominal, 
                             self.value_max_alert, self.value_max] if v is not None]
        
        if len(values) > 1:
            # Vérifier l'ordre croissant
            for i in range(len(values) - 1):
                if values[i] > values[i + 1]:
                    raise ValidationError(
                        'Les valeurs doivent respecter l\'ordre: min ≤ min_alerte ≤ nominale ≤ max_alerte ≤ max'
                    )
    
    def get_status(self, measured_value):
        """Retourne le statut d'une mesure."""
        if self.value_min is not None and measured_value < self.value_min:
            return 'critical_low'
        elif self.value_min_alert is not None and measured_value < self.value_min_alert:
            return 'warning_low'
        elif self.value_max is not None and measured_value > self.value_max:
            return 'critical_high'
        elif self.value_max_alert is not None and measured_value > self.value_max_alert:
            return 'warning_high'
        else:
            return 'ok'
    
    def __str__(self):
        spec_type_display = dict(self.SPEC_TYPES).get(self.spec_type, self.spec_type)
        nominal = f" - Nom: {self.value_nominal}{self.unit}" if self.value_nominal else ""
        return f"{spec_type_display}: {self.name}{nominal}"
