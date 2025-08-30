from django.db import models
from .shift import Shift


class RollManager(models.Manager):
    """Manager personnalisé pour les rouleaux."""
    
    def for_session(self, session_key):
        """Retourne les rouleaux d'une session."""
        return self.filter(session_key=session_key)
    
    def for_shift_id(self, shift_id_str):
        """Retourne les rouleaux d'un poste via son ID string."""
        return self.filter(shift_id_str=shift_id_str)
    
    def pending_association(self):
        """Retourne les rouleaux en attente d'association à un shift."""
        return self.filter(shift__isnull=True, shift_id_str__isnull=False)
    
    def conforming(self):
        """Retourne les rouleaux conformes."""
        return self.filter(status='CONFORME')
    
    def non_conforming(self):
        """Retourne les rouleaux non conformes."""
        return self.filter(status='NON_CONFORME')


class Roll(models.Model):
    """Modèle représentant un rouleau de production."""
    
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
    
    # Identifiant unique
    roll_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="ID Rouleau",
        help_text="Format: OF_NumRouleau (ex: OF12345_001)"
    )
    
    # Relations
    shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rolls',
        verbose_name="Poste de production",
        help_text="Poste associé (sera lié lors de la sauvegarde du poste)"
    )
    
    shift_id_str = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="ID du poste (texte)",
        help_text="ID du poste conservé même après suppression"
    )
    
    session_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Clé de session pour lier au shift en cours"
    )
    
    fabrication_order = models.ForeignKey(
        'planification.FabricationOrder',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='rolls',
        verbose_name="Ordre de fabrication"
    )
    
    # Données de production
    roll_number = models.PositiveIntegerField(
        verbose_name="N° Rouleau",
        null=True,
        blank=True
    )
    
    length = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Longueur (m)"
    )
    
    tube_mass = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Masse tube (g)"
    )
    
    total_mass = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Masse totale (g)"
    )
    
    net_mass = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Masse nette (g)",
        help_text="Masse totale - Masse tube"
    )
    
    # Statut et destination
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='CONFORME',
        verbose_name="Statut"
    )
    
    destination = models.CharField(
        max_length=20,
        choices=DESTINATION_CHOICES,
        default='PRODUCTION',
        verbose_name="Destination"
    )
    
    # Détails de conformité
    has_blocking_defects = models.BooleanField(
        default=False,
        verbose_name="Défauts bloquants"
    )
    
    has_thickness_issues = models.BooleanField(
        default=False,
        verbose_name="Problèmes d'épaisseur"
    )
    
    # Moyennes d'épaisseurs
    avg_thickness_left = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Épaisseur moyenne gauche (mm)"
    )
    
    avg_thickness_right = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Épaisseur moyenne droite (mm)"
    )
    
    # Grammage calculé
    grammage_calc = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Grammage calculé (g/m)",
        help_text="Grammage calculé et sauvegardé"
    )
    
    # Commentaire
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire",
        help_text="Commentaire libre sur le rouleau"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Manager personnalisé
    objects = RollManager()
    
    class Meta:
        verbose_name = "Rouleau"
        verbose_name_plural = "Rouleaux"
        ordering = ['-created_at', '-id']
        unique_together = [['shift', 'roll_number']]
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['fabrication_order', 'roll_number']),
            models.Index(fields=['session_key', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.roll_id} - {self.length}m" if self.length else self.roll_id
    
    def save(self, *args, **kwargs):
        """Génère ou met à jour automatiquement le roll_id."""
        # Toujours recalculer si on a OF et numéro
        if self.fabrication_order and self.roll_number:
            new_roll_id = f"{self.fabrication_order.order_number}_{self.roll_number:03d}"
            # Mettre à jour si différent
            if self.roll_id != new_roll_id:
                self.roll_id = new_roll_id
        elif not self.roll_id:
            # Format alternatif si pas d'OF: ROLL_YYYYMMDD_HHMMSS
            from datetime import datetime
            now = datetime.now()
            self.roll_id = f"ROLL_{now.strftime('%Y%m%d_%H%M%S')}"
        
        super().save(*args, **kwargs)