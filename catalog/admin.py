from django.contrib import admin
from django.utils.html import format_html
from .models import (
    QualityDefectType,
    WcmChecklistTemplate, WcmChecklistItem, WcmChecklistTemplateItem, WcmLostTimeReason,
    SpecItem, ParamItem, ProfileTemplate, ProfileSpecValue, ProfileParamValue
)


# QUALITY - Admin
@admin.register(QualityDefectType)
class QualityDefectTypeAdmin(admin.ModelAdmin):
    """Administration des types de défauts."""
    
    list_display = ['name', 'severity_display', 'threshold_value', 'is_active']
    list_filter = ['severity', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Identification', {
            'fields': ('name', 'description')
        }),
        ('Configuration', {
            'fields': ('severity', 'threshold_value', 'is_active')
        }),
    )
    
    def severity_display(self, obj):
        """Affiche la sévérité avec couleur."""
        colors = {
            'non_blocking': 'green',
            'blocking': 'red',
            'threshold': 'orange'
        }
        color = colors.get(obj.severity, 'black')
        return format_html('<span style="color: {};">{}</span>', 
                          color, obj.get_severity_display())
    severity_display.short_description = "Criticité"


# WCM - Admin
class WcmChecklistTemplateItemInline(admin.TabularInline):
    """Inline pour gérer les items d'un template."""
    model = WcmChecklistTemplateItem
    extra = 1
    fields = ['item', 'order', 'is_required']
    ordering = ['order']
    autocomplete_fields = ['item']
    
    def get_formset(self, request, obj=None, **kwargs):
        """Override pour ajouter un help_text sur le champ order."""
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields['order'].help_text = (
            "Laissez à 0 pour auto-incrémenter. Les ordres doivent être uniques par template."
        )
        return formset


@admin.register(WcmChecklistTemplate)
class WcmChecklistTemplateAdmin(admin.ModelAdmin):
    """Administration des templates de check-list."""
    
    list_display = ['name', 'item_count', 'is_default', 'is_active']
    list_filter = ['is_active', 'is_default']
    search_fields = ['name', 'description']
    ordering = ['name']
    inlines = [WcmChecklistTemplateItemInline]
    
    fieldsets = (
        ('Identification', {
            'fields': ('name', 'description')
        }),
        ('Configuration', {
            'fields': ('is_active', 'is_default')
        }),
    )
    
    def item_count(self, obj):
        """Nombre d'items."""
        return obj.items.count()
    item_count.short_description = "Nb items"


@admin.register(WcmChecklistItem)
class WcmChecklistItemAdmin(admin.ModelAdmin):
    """Administration des items de check-list."""
    
    list_display = ['text', 'category', 'is_active', 'template_count']
    list_filter = ['category', 'is_active']
    search_fields = ['text']
    ordering = ['category', 'text']
    
    fieldsets = (
        ('Identification', {
            'fields': ('text', 'category')
        }),
        ('Configuration', {
            'fields': ('is_active',)
        }),
    )
    
    def template_count(self, obj):
        """Nombre de templates utilisant cet item."""
        return obj.templates.count()
    template_count.short_description = "Utilisé dans"


@admin.register(WcmLostTimeReason)
class WcmLostTimeReasonAdmin(admin.ModelAdmin):
    """Administration des motifs de temps perdu."""
    
    list_display = ['name', 'category', 'is_planned', 'color_display', 'is_active']
    list_filter = ['category', 'is_planned', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['category', 'order', 'name']
    
    fieldsets = (
        ('Identification', {
            'fields': ('name', 'category', 'description')
        }),
        ('Configuration', {
            'fields': ('is_planned', 'is_active', 'order')
        }),
        ('Affichage', {
            'fields': ('color',)
        }),
    )
    
    def color_display(self, obj):
        """Affiche la couleur."""
        return format_html(
            '<span style="background-color: {}; padding: 2px 10px; '
            'border-radius: 3px; color: white;">{}</span>',
            obj.color, obj.color
        )
    color_display.short_description = "Couleur"


# SPECIFICATIONS - Admin
@admin.register(SpecItem)
class SpecItemAdmin(admin.ModelAdmin):
    """Administration des items de spécification."""
    
    list_display = ['name', 'display_name', 'unit', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'display_name']
    ordering = ['order', 'name']
    
    fieldsets = (
        ('Identification', {
            'fields': ('name', 'display_name', 'unit')
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('wide',)
        }),
        ('Configuration', {
            'fields': ('order', 'is_active')
        }),
    )


# PARAMETRES - Admin
@admin.register(ParamItem)
class ParamItemAdmin(admin.ModelAdmin):
    """Administration des items de paramètres machine."""
    
    list_display = ['name', 'display_name', 'category', 'unit', 'order', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'display_name']
    ordering = ['category', 'order', 'name']
    
    fieldsets = (
        ('Identification', {
            'fields': ('name', 'display_name', 'category', 'unit', 'default_value')
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('wide',)
        }),
        ('Configuration', {
            'fields': ('order', 'is_active')
        }),
    )


# PROFILES - Admin
class ProfileSpecValueInline(admin.TabularInline):
    """Inline pour les valeurs de spécifications d'un profil."""
    model = ProfileSpecValue
    extra = 0
    fields = ['spec_item', 'value_min', 'value_min_alert', 'value_nominal', 
              'value_max_alert', 'value_max', 'max_nok', 'is_blocking']
    

class ProfileParamValueInline(admin.TabularInline):
    """Inline pour les valeurs de paramètres d'un profil."""
    model = ProfileParamValue
    extra = 0
    fields = ['param_item', 'value']


@admin.register(ProfileTemplate)
class ProfileTemplateAdmin(admin.ModelAdmin):
    """Administration des templates de profil."""
    
    list_display = ['name', 'spec_count', 'param_count', 'belt_speed_display', 'oee_target', 'is_default', 'is_active']
    list_filter = ['is_active', 'is_default']
    search_fields = ['name', 'description']
    ordering = ['name']
    inlines = [ProfileSpecValueInline, ProfileParamValueInline]
    fieldsets = (
        ('Identification', {
            'fields': ('name', 'description')
        }),
        ('Configuration', {
            'fields': ('is_active', 'is_default')
        }),
        ('Objectifs', {
            'fields': ('oee_target',),
            'description': 'Objectif de performance pour ce profil'
        }),
        ('Paramètres calculés', {
            'fields': ('belt_speed_m_per_minute',),
            'description': 'Valeurs calculées automatiquement à partir des paramètres machine'
        }),
    )
    
    def spec_count(self, obj):
        """Nombre de spécifications."""
        return obj.spec_items.count()
    spec_count.short_description = "Nb specs"
    
    def param_count(self, obj):
        """Nombre de paramètres machine."""
        return obj.param_items.count()
    param_count.short_description = "Nb params"
    
    def belt_speed_display(self, obj):
        """Affiche la vitesse tapis en m/min."""
        if obj.belt_speed_m_per_minute:
            return f"{obj.belt_speed_m_per_minute} m/min"
        return "-"
    belt_speed_display.short_description = "Vitesse tapis"