from django.db import models


class Operator(models.Model):
    """Modèle représentant un opérateur de production."""
    
    # Identification
    first_name = models.CharField(
        max_length=50,
        verbose_name="Prénom",
        help_text="Prénom de l'opérateur"
    )
    
    last_name = models.CharField(
        max_length=50,
        verbose_name="Nom",
        help_text="Nom de famille de l'opérateur"
    )
    
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Matricule",
        help_text="Matricule employé (généré automatiquement si non fourni)"
    )
    
    # Statut
    training_completed = models.BooleanField(
        default=False,
        verbose_name="Formation complétée",
        help_text="Indique si l'opérateur a terminé sa formation"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Opérateur actif dans le système"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Opérateur"
        verbose_name_plural = "Opérateurs"
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['is_active', 'last_name']),
            models.Index(fields=['employee_id']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        """Retourne le nom complet de l'opérateur."""
        return f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        """Génère automatiquement l'employee_id si non fourni."""
        # Générer l'employee_id si non fourni
        if not self.employee_id:
            # Format: PrenomNOM (nom en majuscules)
            self.employee_id = f"{self.first_name}{self.last_name.upper()}".replace(' ', '')
        
        super().save(*args, **kwargs)
    


class FabricationOrder(models.Model):
    """Modèle représentant un ordre de fabrication."""
    
    # Identification
    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Numéro d'OF",
        help_text="Numéro d'ordre de fabrication (ex: OF12345)"
    )
    
    
    # Quantités et dimensions
    required_length = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Longueur à produire (m)",
        help_text="Longueur totale à produire - vide = illimité"
    )
    
    target_roll_length = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Longueur par rouleau (m)",
        help_text="Longueur souhaitée par rouleau - vide = illimité"
    )
    
    # Options
    for_cutting = models.BooleanField(
        default=False,
        verbose_name="Pour la découpe",
        help_text="Indique si cet OF est destiné à la découpe"
    )
    
    terminated = models.BooleanField(
        default=False,
        verbose_name="Terminé",
        help_text="Indique si cet OF est terminé"
    )
    
    # Dates
    creation_date = models.DateField(
        auto_now_add=True,
        verbose_name="Date de création",
        help_text="Date de création de l'OF"
    )
    
    due_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date d'échéance",
        help_text="Date d'échéance (optionnelle)"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Ordre de Fabrication"
        verbose_name_plural = "Ordres de Fabrication"
        ordering = ['-creation_date', '-created_at']
        indexes = [
            models.Index(fields=['terminated', '-creation_date']),
            models.Index(fields=['order_number']),
        ]
    
    def __str__(self):
        status = " (Terminé)" if self.terminated else ""
        return f"{self.order_number}{status}"
    
