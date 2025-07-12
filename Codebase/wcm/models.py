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