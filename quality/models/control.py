from django.db import models


class Controls(models.Model):
    """Contrôles qualité effectués pendant la production."""
    
    # Relations
    shift = models.ForeignKey(
        'production.Shift',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='quality_controls',
        verbose_name="Poste"
    )
    
    session_key = models.CharField(
        max_length=255,
        verbose_name="Clé de session",
        help_text="Clé de session pour lier au shift en cours"
    )
    
    # Contrôles Micronnaire Gauche
    micrometer_left_1 = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name="Micronnaire Gauche #1"
    )
    
    micrometer_left_2 = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name="Micronnaire Gauche #2"
    )
    
    micrometer_left_3 = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name="Micronnaire Gauche #3"
    )
    
    micrometer_left_avg = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name="Micronnaire Gauche Moyenne"
    )
    
    # Contrôles Micronnaire Droite
    micrometer_right_1 = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name="Micronnaire Droite #1"
    )
    
    micrometer_right_2 = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name="Micronnaire Droite #2"
    )
    
    micrometer_right_3 = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name="Micronnaire Droite #3"
    )
    
    micrometer_right_avg = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name="Micronnaire Droite Moyenne"
    )
    
    # Extrait Sec
    dry_extract = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name="Extrait Sec (%)"
    )
    
    dry_extract_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Heure Extrait Sec"
    )
    
    # Masses Surfaciques Gauche
    surface_mass_gg = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Masse Surfacique GG (g/25cm²)"
    )
    
    surface_mass_gc = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Masse Surfacique GC (g/25cm²)"
    )
    
    surface_mass_left_avg = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Masse Surfacique Gauche Moyenne"
    )
    
    # Masses Surfaciques Droite
    surface_mass_dc = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Masse Surfacique DC (g/25cm²)"
    )
    
    surface_mass_dd = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Masse Surfacique DD (g/25cm²)"
    )
    
    surface_mass_right_avg = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Masse Surfacique Droite Moyenne"
    )
    
    # LOI
    loi_given = models.BooleanField(
        default=False,
        verbose_name="LOI donnée"
    )
    
    loi_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Heure LOI"
    )
    
    # Validation globale
    is_valid = models.BooleanField(
        default=True,
        verbose_name="Contrôles valides",
        help_text="Indique si tous les contrôles sont dans les tolérances"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date/heure du contrôle"
    )
    
    created_by = models.ForeignKey(
        'planification.Operator',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Contrôlé par"
    )
    
    class Meta:
        verbose_name = "Contrôle qualité"
        verbose_name_plural = "Contrôles qualité"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shift', '-created_at']),
            models.Index(fields=['session_key', '-created_at']),
            models.Index(fields=['is_valid', '-created_at']),
        ]
    
    def __str__(self):
        if self.shift:
            return f"Contrôles {self.shift.shift_id} - {self.created_at.strftime('%H:%M')}"
        return f"Contrôles session {self.session_key} - {self.created_at.strftime('%H:%M')}"