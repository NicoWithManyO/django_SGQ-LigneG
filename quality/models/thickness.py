from django.db import models


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
    
    # Relations
    roll = models.ForeignKey(
        'production.Roll',
        on_delete=models.CASCADE,
        related_name='thickness_measurements',
        verbose_name="Rouleau"
    )
    
    # Position et point de mesure
    meter_position = models.PositiveIntegerField(
        verbose_name="Position (m)",
        help_text="Position de la mesure en mètres"
    )
    
    measurement_point = models.CharField(
        max_length=2,
        choices=MEASUREMENT_POINTS,
        verbose_name="Point de mesure"
    )
    
    # Valeur mesurée
    thickness_value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Épaisseur (mm)"
    )
    
    # Type de mesure
    is_catchup = models.BooleanField(
        default=False,
        verbose_name="Mesure de rattrapage",
        help_text="Indique si c'est une mesure de rattrapage"
    )
    
    # Validation
    is_within_tolerance = models.BooleanField(
        default=True,
        verbose_name="Dans les tolérances"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Mesure d'épaisseur"
        verbose_name_plural = "Mesures d'épaisseur"
        ordering = ['roll', 'meter_position', 'measurement_point']
        indexes = [
            models.Index(fields=['roll', 'meter_position']),
            models.Index(fields=['roll', 'is_catchup']),
            models.Index(fields=['is_within_tolerance', '-created_at']),
        ]
    
    def __str__(self):
        catchup_str = " (rattrapage)" if self.is_catchup else ""
        return f"{self.roll.roll_id} - {self.measurement_point} à {self.meter_position}m: {self.thickness_value}mm{catchup_str}"