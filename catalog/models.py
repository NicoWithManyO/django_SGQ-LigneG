from django.db import models


# QUALITY - Modèles de référence
class QualityDefectType(models.Model):
    """Types de défauts avec leur criticité."""
    
    SEVERITY_CHOICES = [
        ('non_blocking', 'Non bloquant'),
        ('blocking', 'Bloquant'),
        ('threshold', 'Bloquant selon seuil'),
    ]
    
    # Identification
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom du défaut"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Description détaillée du défaut"
    )
    
    # Criticité
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        verbose_name="Criticité",
        help_text="Niveau de criticité du défaut"
    )
    
    threshold_value = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Valeur seuil",
        help_text="Nombre max avant blocage (si criticité=threshold)"
    )
    
    # État
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Type de défaut qualité"
        verbose_name_plural = "Types de défauts qualité"
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'severity']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_severity_display()})"


# WCM - Modèles de référence
class WcmChecklistTemplate(models.Model):
    """Templates de check-lists réutilisables."""
    
    # Identification
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom du template"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Description du template et de son usage"
    )
    
    # Items sélectionnés pour ce template
    items = models.ManyToManyField(
        'WcmChecklistItem',
        through='WcmChecklistTemplateItem',
        related_name='templates',
        verbose_name="Items de la checklist"
    )
    
    # Configuration
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    is_default = models.BooleanField(
        default=False,
        verbose_name="Template par défaut"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Template de check-list WCM"
        verbose_name_plural = "Templates de check-list WCM"
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'is_default']),
        ]
    
    def __str__(self):
        default_str = " (Par défaut)" if self.is_default else ""
        return f"{self.name}{default_str}"


class WcmChecklistItem(models.Model):
    """Items de check-list réutilisables (catalogue)."""
    
    # Contenu
    text = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Texte de l'item",
        help_text="Question ou point à vérifier"
    )
    
    # Catégorie optionnelle
    category = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Catégorie",
        help_text="Ex: Sécurité, Production, Qualité"
    )
    
    # Configuration
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Item de check-list WCM"
        verbose_name_plural = "Items de check-list WCM"
        ordering = ['category', 'text']
        indexes = [
            models.Index(fields=['is_active', 'category']),
        ]
    
    def __str__(self):
        return self.text


class WcmChecklistTemplateItem(models.Model):
    """Table intermédiaire pour gérer l'ordre des items dans un template."""
    
    template = models.ForeignKey(
        WcmChecklistTemplate,
        on_delete=models.CASCADE,
        verbose_name="Template"
    )
    
    item = models.ForeignKey(
        WcmChecklistItem,
        on_delete=models.CASCADE,  # Si on supprime un item, supprimer ses associations aux templates
        verbose_name="Item"
    )
    
    order = models.IntegerField(
        default=0,
        verbose_name="Ordre d'affichage"
    )
    
    is_required = models.BooleanField(
        default=True,
        verbose_name="Obligatoire",
        help_text="Cet item doit-il obligatoirement être complété?"
    )
    
    class Meta:
        verbose_name = "Item de template"
        verbose_name_plural = "Items de template"
        ordering = ['template', 'order']
        unique_together = [['template', 'order']]
    
    def __str__(self):
        return f"{self.template.name} - {self.order}. {self.item.text}"
    
    def save(self, *args, **kwargs):
        """Override save pour auto-incrémenter l'ordre si nécessaire."""
        # Si pas d'ordre défini ou ordre=0 avec des items existants
        if self.order == 0 and not self.pk:
            # Chercher le max order pour ce template
            max_order = WcmChecklistTemplateItem.objects.filter(
                template=self.template
            ).aggregate(models.Max('order'))['order__max']
            
            # Si des items existent déjà, prendre le prochain numéro
            if max_order is not None:
                self.order = max_order + 1
        
        super().save(*args, **kwargs)


class WcmLostTimeReason(models.Model):
    """Motifs de temps perdus configurables."""
    
    CATEGORY_CHOICES = [
        ('arret_programme', 'Arrêt programmé'),
        ('panne', 'Panne'),
        ('changement_serie', 'Changement de série'),
        ('reglage', 'Réglage'),
        ('maintenance', 'Maintenance'),
        ('qualite', 'Problème qualité'),
        ('approvisionnement', 'Approvisionnement'),
        ('autre', 'Autre'),
    ]
    
    # Identification
    name = models.CharField(
        max_length=100,
        verbose_name="Nom du motif"
    )
    
    # Catégorisation
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        null=True,
        blank=True,
        verbose_name="Catégorie"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    # Configuration
    is_planned = models.BooleanField(
        default=False,
        verbose_name="Arrêt planifié",
        help_text="Indique si c'est un arrêt planifié"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    # Affichage
    order = models.IntegerField(
        default=100,
        verbose_name="Ordre d'affichage"
    )
    
    color = models.CharField(
        max_length=7,
        default='#6c757d',
        verbose_name="Couleur (hex)",
        help_text="Couleur pour l'affichage dans l'interface"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Motif de temps perdu WCM"
        verbose_name_plural = "Motifs de temps perdus WCM"
        ordering = ['category', 'order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'category']),
        ]
    
    def __str__(self):
        return self.name


# SPECIFICATIONS - Modèles pour les spécifications
class SpecItem(models.Model):
    """Item de spécification réutilisable (catalogue des types de specs)."""
    
    # Identification
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Nom technique",
        help_text="Ex: thickness, micrometer, surface_mass"
    )
    
    display_name = models.CharField(
        max_length=100,
        verbose_name="Nom d'affichage",
        help_text="Ex: Épaisseur, Micronnaire, Masse surfacique"
    )
    
    unit = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Unité",
        help_text="Ex: mm, g/m², %"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    # Configuration
    order = models.IntegerField(
        default=0,
        verbose_name="Ordre d'affichage"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Item de spécification"
        verbose_name_plural = "Items de spécification"
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.display_name} ({self.unit})" if self.unit else self.display_name


# PARAMETRES MACHINE - Modèles pour les paramètres
class ParamItem(models.Model):
    """Item de paramètre machine réutilisable."""
    
    CATEGORY_CHOICES = [
        ('fibrage', 'Fibrage'),
        ('ensimeuse', 'Ensimeuse'),
        ('autre', 'Autre'),
    ]
    
    # Identification
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Nom technique",
        help_text="Ex: oxygen_primary, belt_speed"
    )
    
    display_name = models.CharField(
        max_length=100,
        verbose_name="Nom d'affichage",
        help_text="Ex: Oxygène primaire, Vitesse tapis"
    )
    
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name="Catégorie"
    )
    
    unit = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Unité",
        help_text="Ex: l/min, m/h"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    # Valeur par défaut
    default_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Valeur par défaut",
        help_text="Valeur par défaut pour ce paramètre"
    )
    
    # Configuration
    order = models.IntegerField(
        default=0,
        verbose_name="Ordre d'affichage"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Item de paramètre machine"
        verbose_name_plural = "Items de paramètres machine"
        ordering = ['category', 'order', 'name']
    
    def __str__(self):
        return f"[{self.get_category_display()}] {self.display_name}"


# PROFILES - Modèles pour les profils de production
class ProfileTemplate(models.Model):
    """Template de profil de production réutilisable."""
    
    # Identification
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom du profil",
        help_text="Ex: 80g/m², 40g/m²"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Description du profil et de son usage"
    )
    
    # Relations avec tables intermédiaires
    spec_items = models.ManyToManyField(
        SpecItem,
        through='ProfileSpecValue',
        blank=True,
        related_name='profile_templates',
        verbose_name="Spécifications",
        help_text="Spécifications associées à ce profil"
    )
    
    param_items = models.ManyToManyField(
        ParamItem,
        through='ProfileParamValue',
        blank=True,
        related_name='profile_templates',
        verbose_name="Paramètres machine",
        help_text="Paramètres machine associés à ce profil"
    )
    
    # Configuration
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    is_default = models.BooleanField(
        default=False,
        verbose_name="Profil par défaut"
    )
    
    # Champ calculé pour la vitesse tapis
    belt_speed_m_per_minute = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Vitesse tapis (m/min)",
        help_text="Vitesse tapis convertie en m/min (calculée automatiquement)"
    )
    
    oee_target = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=85.00,
        verbose_name="Objectif TRS (%)",
        help_text="Objectif de Taux de Rendement Synthétique (OEE) en pourcentage"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Template de profil"
        verbose_name_plural = "Templates de profil"
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'is_default']),
        ]
    
    def __str__(self):
        default_str = " (Par défaut)" if self.is_default else ""
        return f"{self.name}{default_str}"
    
    def save(self, *args, **kwargs):
        """Override save pour calculer belt_speed_m_per_minute avant sauvegarde."""
        # Calculer la vitesse en m/min AVANT de sauvegarder
        try:
            # Chercher le paramètre vitesse tapis pour ce profil
            from django.db.models import Q
            
            # Si l'objet a déjà un ID, on peut chercher dans les relations
            if self.pk:
                belt_speed_param = self.profileparamvalue_set.filter(
                    Q(param_item__name__iexact='vitesse_tapis') |
                    Q(param_item__name__iexact='vitesse tapis') |
                    Q(param_item__name__iexact='belt_speed') |
                    Q(param_item__name__iexact='speed_belt') |
                    Q(param_item__display_name__icontains='vitesse') & Q(param_item__display_name__icontains='tapis')
                ).first()
                
                if belt_speed_param and belt_speed_param.value:
                    # Convertir de m/h en m/min
                    self.belt_speed_m_per_minute = round(float(belt_speed_param.value) / 60, 2)
                else:
                    self.belt_speed_m_per_minute = None
        except Exception as e:
            print(f"Erreur lors du calcul de belt_speed_m_per_minute: {e}")
        
        # Sauvegarder normalement
        super().save(*args, **kwargs)


class ProfileSpecValue(models.Model):
    """Valeurs de spécification pour un profil."""
    
    # Relations
    profile = models.ForeignKey(
        ProfileTemplate,
        on_delete=models.CASCADE,
        verbose_name="Profil"
    )
    
    spec_item = models.ForeignKey(
        SpecItem,
        on_delete=models.CASCADE,
        verbose_name="Spécification"
    )
    
    # Valeurs
    value_min = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Valeur minimale",
        help_text="Seuil minimum critique"
    )
    
    value_min_alert = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Alerte minimale",
        help_text="Seuil d'alerte bas"
    )
    
    value_nominal = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        default=0,
        verbose_name="Valeur nominale",
        help_text="Valeur cible"
    )
    
    value_max_alert = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Alerte maximale",
        help_text="Seuil d'alerte haut"
    )
    
    value_max = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Valeur maximale",
        help_text="Seuil maximum critique"
    )
    
    # Configuration
    max_nok = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Max NOK",
        help_text="Nombre max de mesures NOK avant blocage"
    )
    
    is_blocking = models.BooleanField(
        default=False,
        verbose_name="Bloquant",
        help_text="Cette spec peut-elle bloquer la production?"
    )
    
    class Meta:
        verbose_name = "Valeur de spécification"
        verbose_name_plural = "Valeurs de spécification"
        unique_together = [['profile', 'spec_item']]
    
    def __str__(self):
        return f"{self.profile.name} - {self.spec_item.display_name}"


class ProfileParamValue(models.Model):
    """Valeurs de paramètre machine pour un profil."""
    
    # Relations
    profile = models.ForeignKey(
        ProfileTemplate,
        on_delete=models.CASCADE,
        verbose_name="Profil"
    )
    
    param_item = models.ForeignKey(
        ParamItem,
        on_delete=models.CASCADE,
        verbose_name="Paramètre"
    )
    
    # Valeur
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Valeur",
        help_text="Valeur du paramètre pour ce profil"
    )
    
    class Meta:
        verbose_name = "Valeur de paramètre"
        verbose_name_plural = "Valeurs de paramètres"
        unique_together = [['profile', 'param_item']]
    
    def __str__(self):
        return f"{self.profile.name} - {self.param_item.display_name}: {self.value}"
    
    def save(self, *args, **kwargs):
        """Override save pour mettre à jour belt_speed_m_per_minute du profil si nécessaire."""
        super().save(*args, **kwargs)
        
        # Si c'est un paramètre de vitesse tapis, forcer le recalcul du profil
        if self.param_item.name.lower() in ['belt_speed', 'speed_belt', 'vitesse_tapis', 'vitesse tapis']:
            # Forcer le recalcul en sauvegardant le profil
            self.profile.save()