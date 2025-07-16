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



class Specification(models.Model):
    """Spécifications générales pour tous types de contrôles qualité."""
    
    SPEC_TYPES = [
        ('thickness', 'Épaisseur'),
        ('micrometer', 'Micronnaire'),
        ('surface_mass', 'Masse surfacique (g/25cm²)'),
        ('dry_extract', 'Extrait sec'),
        ('global_surface_mass', 'Masse surfacique globale (g/m²)'),
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
        # Convertir la valeur mesurée en float pour la comparaison
        try:
            value = float(measured_value)
        except (TypeError, ValueError):
            return 'ok'
            
        if self.value_min is not None and value < float(self.value_min):
            return 'critical_low'
        elif self.value_min_alert is not None and value < float(self.value_min_alert):
            return 'warning_low'
        elif self.value_max is not None and value > float(self.value_max):
            return 'critical_high'
        elif self.value_max_alert is not None and value > float(self.value_max_alert):
            return 'warning_high'
        else:
            return 'ok'
    
    def __str__(self):
        spec_type_display = dict(self.SPEC_TYPES).get(self.spec_type, self.spec_type)
        nominal = f" - Nom: {self.value_nominal}{self.unit}" if self.value_nominal else ""
        return f"{spec_type_display}: {self.name}{nominal}"
