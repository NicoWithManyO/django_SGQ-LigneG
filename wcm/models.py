from django.db import models


class Mode(models.Model):
    """Modes de fonctionnement de la machine."""
    
    # Identification
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Nom du mode",
        help_text="Ex: Permissif, Dégradé, Maintenance"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Description détaillée du mode et de ses implications"
    )
    
    # État
    is_enabled = models.BooleanField(
        default=False,
        verbose_name="Activé",
        help_text="Indique si ce mode est actuellement activé"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Mode disponible dans le système"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Mode de fonctionnement"
        verbose_name_plural = "Modes de fonctionnement"
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_enabled', 'is_active']),
        ]
    
    def __str__(self):
        return self.name


class MoodCounter(models.Model):
    """Compteur d'humeur pour suivi anonyme."""
    
    MOOD_CHOICES = [
        ('no_response', 'Sans réponse'),
        ('happy', 'Content'),
        ('unhappy', 'Pas content'),
        ('neutral', 'Neutre'),
    ]
    
    # Type d'humeur
    mood_type = models.CharField(
        max_length=20,
        choices=MOOD_CHOICES,
        unique=True,
        verbose_name="Type d'humeur"
    )
    
    # Compteur
    count = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de fois sélectionnée"
    )
    
    # Date du dernier reset
    last_reset_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date du dernier reset",
        help_text="Date et heure du dernier reset du compteur"
    )
    
    # Métadonnées
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Compteur d'humeur"
        verbose_name_plural = "Compteurs d'humeur"
        ordering = ['mood_type']
    
    def __str__(self):
        return f"{self.get_mood_type_display()} ({self.count})"
    
    @classmethod
    def get_percentages(cls):
        """Calcule les pourcentages pour chaque type d'humeur."""
        counters = cls.objects.all()
        total = sum(counter.count for counter in counters)
        
        if total == 0:
            return {counter.mood_type: 0 for counter in counters}
        
        percentages = {}
        for counter in counters:
            percentage = round((counter.count / total) * 100, 1)
            percentages[counter.mood_type] = percentage
        
        return percentages
    
    @classmethod
    def reset_all_counters(cls):
        """Reset tous les compteurs à zéro et enregistre la date."""
        from django.utils import timezone
        now = timezone.now()
        
        # Mettre à jour tous les compteurs
        cls.objects.all().update(
            count=0,
            last_reset_at=now
        )
        
        return now


class LostTimeEntry(models.Model):
    """Entrées de temps d'arrêt."""
    
    # Relations
    shift = models.ForeignKey(
        'production.Shift',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='lost_time_entries',
        verbose_name="Poste",
        help_text="Poste associé (si déjà sauvegardé)"
    )
    
    session_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Clé de session pour lier au shift en cours"
    )
    
    # Motif d'arrêt
    reason = models.ForeignKey(
        'catalog.WcmLostTimeReason',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='entries',
        verbose_name="Motif",
        help_text="Motif de l'arrêt depuis le catalogue"
    )
    
    motif = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Motif (texte libre)",
        help_text="Motif d'arrêt en texte libre (déprécié)"
    )
    
    # Détails
    comment = models.TextField(
        blank=True,
        verbose_name="Commentaire"
    )
    
    duration = models.PositiveIntegerField(
        verbose_name="Durée (minutes)",
        help_text="Durée de l'arrêt en minutes"
    )
    
    # Traçabilité
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'planification.Operator',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Créé par"
    )
    
    class Meta:
        verbose_name = "Temps d'arrêt"
        verbose_name_plural = "Temps d'arrêt"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shift', '-created_at']),
            models.Index(fields=['session_key', '-created_at']),
            models.Index(fields=['reason', '-created_at']),
        ]
    
    def __str__(self):
        if self.reason:
            return f"{self.reason.name} - {self.duration} min"
        elif self.motif:
            return f"{self.motif} - {self.duration} min"
        return f"Arrêt - {self.duration} min"



class ChecklistResponse(models.Model):
    """Toutes les réponses de checklist pour un poste."""
    
    # Relations
    shift = models.OneToOneField(
        'production.Shift',
        on_delete=models.CASCADE,
        related_name='checklist_response',
        verbose_name="Poste"
    )
    
    operator = models.ForeignKey(
        'planification.Operator',
        on_delete=models.PROTECT,
        related_name='checklist_responses',
        verbose_name="Opérateur",
        null=True  # Temporaire pour la migration
    )
    
    # Réponses stockées en JSON
    responses = models.JSONField(
        default=dict,
        verbose_name="Réponses",
        help_text="Format: {item_id: 'ok'/'nok'/'na'}"
    )
    
    # Signature opérateur
    operator_signature = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Signature opérateur (initiales)",
        help_text="Initiales de l'opérateur"
    )
    
    operator_signature_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date signature opérateur"
    )
    
    # Visa management
    management_visa = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Visa management",
        help_text="Visa du responsable ayant validé la checklist"
    )
    
    management_visa_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date visa management"
    )
    
    # Traçabilité
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Réponse check-list"
        verbose_name_plural = "Réponses check-list"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shift']),
        ]
    
    def __str__(self):
        return f"Checklist - {self.shift}"


class TRS(models.Model):
    """Taux de Rendement Synthétique (OEE) calculé et stocké pour chaque poste."""
    
    # Lien vers le shift
    shift = models.OneToOneField(
        'production.Shift',
        on_delete=models.CASCADE,
        related_name='trs',
        verbose_name="Poste"
    )
    
    # === TEMPS ===
    opening_time = models.DurationField(
        verbose_name="Temps d'ouverture",
        help_text="Temps total entre début et fin du poste"
    )
    
    availability_time = models.DurationField(
        verbose_name="Temps disponible",
        help_text="Temps d'ouverture - Temps perdu"
    )
    
    lost_time = models.DurationField(
        verbose_name="Temps perdu",
        help_text="Somme des temps d'arrêt"
    )
    
    # === PRODUCTION ===
    total_length = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Longueur totale (m)",
        help_text="Longueur totale produite"
    )
    
    ok_length = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Longueur conforme (m)",
        help_text="Longueur de production conforme"
    )
    
    nok_length = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Longueur non conforme (m)",
        help_text="Longueur de production non conforme"
    )
    
    raw_waste_length = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Déchet brut (m)",
        help_text="Longueur de déchet brut"
    )
    
    # === MÉTRIQUES TRS CALCULÉES ===
    trs_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name="TRS (%)",
        help_text="Taux de Rendement Synthétique (OEE)"
    )
    
    availability_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name="Disponibilité (%)",
        help_text="(Temps disponible / Temps d'ouverture) × 100"
    )
    
    performance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name="Performance (%)",
        help_text="(Production réelle / Production théorique) × 100"
    )
    
    quality_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name="Qualité (%)",
        help_text="(Longueur OK / Longueur totale) × 100"
    )
    
    # === DONNÉES DE CALCUL ===
    theoretical_production = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Production théorique (m)",
        help_text="Temps disponible × Vitesse tapis"
    )
    
    # === PROFIL UTILISÉ (pour historisation) ===
    profile_name = models.CharField(
        max_length=100,
        verbose_name="Profil utilisé",
        help_text="Nom du profil de production utilisé"
    )
    
    belt_speed_m_per_min = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Vitesse tapis (m/min)",
        help_text="Vitesse tapis du profil utilisé"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "TRS"
        verbose_name_plural = "TRS"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shift']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"TRS {self.shift.shift_id} - {self.trs_percentage}%"