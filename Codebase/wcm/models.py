from django.db import models


class ChecklistTemplate(models.Model):
    """Template de check-list réutilisable."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom du template")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    is_default = models.BooleanField(default=False, verbose_name="Template par défaut")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Template de check-list"
        verbose_name_plural = "Templates de check-list"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'un seul template par défaut
        if self.is_default:
            ChecklistTemplate.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class ChecklistItem(models.Model):
    """Item individuel d'un template de check-list."""
    template = models.ForeignKey(ChecklistTemplate, on_delete=models.CASCADE, 
                               related_name='items', verbose_name="Template")
    text = models.CharField(max_length=200, verbose_name="Texte de l'item")
    order = models.IntegerField(default=0, verbose_name="Ordre d'affichage")
    is_required = models.BooleanField(default=True, verbose_name="Obligatoire")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Item de check-list"
        verbose_name_plural = "Items de check-list"
        ordering = ['template', 'order', 'text']
        unique_together = [['template', 'order']]
    
    def __str__(self):
        return f"{self.template.name} - {self.order}. {self.text}"
    
    def save(self, *args, **kwargs):
        # Auto-incrémenter l'ordre si non spécifié
        if not self.order:
            max_order = ChecklistItem.objects.filter(template=self.template).aggregate(
                models.Max('order')
            )['order__max'] or 0
            self.order = max_order + 10
        super().save(*args, **kwargs)


class ChecklistResponse(models.Model):
    """Réponse à un item de check-list pour un shift donné."""
    
    RESPONSE_CHOICES = [
        ('ok', 'OK'),
        ('na', 'N/A'),
        ('nok', 'NOK'),
    ]
    
    shift = models.ForeignKey('production.Shift', on_delete=models.CASCADE,
                            related_name='checklist_responses', verbose_name="Poste")
    item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE,
                           verbose_name="Item de check-list")
    response = models.CharField(max_length=3, choices=RESPONSE_CHOICES,
                              verbose_name="Réponse")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Réponse check-list"
        verbose_name_plural = "Réponses check-list"
        unique_together = [['shift', 'item']]
        ordering = ['shift', 'item__order']
    
    def __str__(self):
        return f"{self.shift} - {self.item.text}: {self.get_response_display()}"


class MachineParametersHistory(models.Model):
    """Historique des modifications des paramètres machine."""
    
    # Référence au shift en cours au moment de la modification
    shift = models.ForeignKey('production.Shift', on_delete=models.SET_NULL, 
                            null=True, blank=True,
                            related_name='machine_parameters_history',
                            verbose_name="Poste en cours")
    
    # Horodatage de la modification
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Date/heure de modification")
    
    # Opérateur qui a fait la modification
    modified_by = models.ForeignKey('core.Operator', on_delete=models.SET_NULL,
                                  null=True, blank=True,
                                  verbose_name="Modifié par")
    
    # Nom du paramètre pour identification
    parameter_name = models.CharField(max_length=100, verbose_name="Nom du paramètre")
    
    # Valeurs avant/après
    old_value = models.DecimalField(max_digits=10, decimal_places=2, 
                                   null=True, blank=True,
                                   verbose_name="Ancienne valeur")
    new_value = models.DecimalField(max_digits=10, decimal_places=2,
                                   verbose_name="Nouvelle valeur")
    
    # Type de paramètre pour faciliter les requêtes
    PARAMETER_TYPE_CHOICES = [
        ('oxygen_primary', 'Oxygène primaire'),
        ('oxygen_secondary', 'Oxygène secondaire'),
        ('propane_primary', 'Propane primaire'),
        ('propane_secondary', 'Propane secondaire'),
        ('speed_primary', 'Vitesse primaire'),
        ('speed_secondary', 'Vitesse secondaire'),
        ('belt_speed', 'Vitesse bande'),
    ]
    parameter_type = models.CharField(max_length=50, choices=PARAMETER_TYPE_CHOICES,
                                    verbose_name="Type de paramètre")
    
    # Commentaire optionnel
    comment = models.TextField(blank=True, verbose_name="Commentaire")
    
    # Référence aux paramètres machine complets au moment du changement
    machine_parameters = models.ForeignKey('production.MachineParameters',
                                         on_delete=models.SET_NULL,
                                         null=True, blank=True,
                                         verbose_name="Paramètres machine")
    
    class Meta:
        verbose_name = "Historique des paramètres machine"
        verbose_name_plural = "Historiques des paramètres machine"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['shift', '-timestamp']),
            models.Index(fields=['parameter_type', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.parameter_name}: {self.old_value} → {self.new_value} ({self.timestamp.strftime('%d/%m/%Y %H:%M')})"