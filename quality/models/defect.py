from django.db import models


class RollDefect(models.Model):
    """Défauts constatés sur les rouleaux."""
    
    POSITION_SIDE_CHOICES = [
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
        related_name='defects',
        verbose_name="Rouleau"
    )
    
    defect_type = models.ForeignKey(
        'catalog.QualityDefectType',
        on_delete=models.PROTECT,
        related_name='occurrences',
        verbose_name="Type de défaut"
    )
    
    # Position sur le rouleau
    meter_position = models.PositiveIntegerField(
        verbose_name="Position (m)",
        help_text="Position du défaut en mètres depuis le début"
    )
    
    side_position = models.CharField(
        max_length=10,  # Garder 10 pour la migration
        choices=POSITION_SIDE_CHOICES,
        verbose_name="Position transversale",
        help_text="Position transversale du défaut sur la laize"
    )
    
    # Détails
    comment = models.TextField(
        blank=True,
        verbose_name="Commentaire",
        help_text="Détails supplémentaires sur le défaut"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Défaut rouleau"
        verbose_name_plural = "Défauts rouleaux"
        ordering = ['roll', 'meter_position']
        unique_together = [['roll', 'meter_position', 'side_position', 'defect_type']]
        indexes = [
            models.Index(fields=['roll', 'meter_position']),
            models.Index(fields=['defect_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.roll.roll_id} - {self.defect_type.name} à {self.meter_position}m ({self.get_side_position_display()})"