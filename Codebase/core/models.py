from django.db import models
from django.core.exceptions import ValidationError


class FabricationOrder(models.Model):
    """Modèle représentant un ordre de fabrication."""
    
    # Identifiants
    order_number = models.CharField(max_length=50, unique=True, help_text="Numéro d'ordre de fabrication saisi manuellement")
    
    # Quantités et dimensions
    required_length = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        help_text="Longueur totale à produire (en mètres) - 0 = illimité"
    )
    
    target_roll_length = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        help_text="Longueur souhaitée par rouleau (ex: 20m) - 0 = illimité"
    )
    
    # Options de production
    for_cutting = models.BooleanField(default=False, verbose_name="Pour la découpe", 
                                     help_text="Indique si cet ordre de fabrication est destiné à la découpe")
    terminated = models.BooleanField(default=False, verbose_name="Terminé", 
                                   help_text="Indique si cet ordre de fabrication est terminé")
    
    # Dates
    creation_date = models.DateField(auto_now_add=True, help_text="Date de création de l'OF")
    due_date = models.DateField(blank=True, null=True, help_text="Date d'échéance (optionnelle)")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Ordre de Fabrication"
        verbose_name_plural = "Ordres de Fabrication"
        ordering = ['-creation_date', '-created_at']
    
    def clean(self):
        """Validation métier du modèle."""
        super().clean()
        
        if self.required_length is not None and self.required_length < 0:
            raise ValidationError({
                'required_length': 'La longueur requise doit être supérieure ou égale à 0 (0 = illimité)'
            })
        
        if self.target_roll_length is not None and self.target_roll_length < 0:
            raise ValidationError({
                'target_roll_length': 'La longueur cible par rouleau doit être supérieure ou égale à 0 (0 = illimité)'
            })
        
        # Vérifier que la longueur cible est cohérente avec la longueur totale (sauf si 0 = illimité)
        if (self.required_length is not None and self.target_roll_length is not None and
            self.required_length > 0 and self.target_roll_length > 0 and
            self.target_roll_length > self.required_length):
            raise ValidationError({
                'target_roll_length': 'La longueur par rouleau ne peut pas être supérieure à la longueur totale'
            })
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec validation."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"OF {self.order_number}"


class Operator(models.Model):
    """Modèle représentant un opérateur de production."""
    
    # Attributs principaux
    first_name = models.CharField(max_length=50, help_text="Prénom de l'opérateur")
    last_name = models.CharField(max_length=50, help_text="Nom de l'opérateur")
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True,
                                  help_text="Matricule employé (optionnel)")
    training_completed = models.BooleanField(default=False, 
                                           help_text="Formation terminée")
    is_active = models.BooleanField(default=True, 
                                   help_text="Opérateur actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Opérateur"
        verbose_name_plural = "Opérateurs"
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        """Retourne le nom complet de l'opérateur."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name_no_space(self):
        """Retourne le nom complet sans espaces pour les IDs."""
        return f"{self.first_name}{self.last_name}"
    
    def save(self, *args, **kwargs):
        """Génère automatiquement l'employee_id si non fourni."""
        if not self.employee_id:
            # Format: PrenomNOM (NOM en majuscules)
            self.employee_id = f"{self.first_name}{self.last_name.upper()}"
        super().save(*args, **kwargs)
