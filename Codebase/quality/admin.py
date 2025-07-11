from django.contrib import admin
from .models import DefectType, Specification

# Configuration admin pour l'application quality
# Contrôles qualité, mesures et défauts


@admin.register(DefectType)
class DefectTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'severity', 'threshold_value', 'is_active', 'created_at']
    list_filter = ['severity', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Criticité', {
            'fields': ('severity', 'threshold_value')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )




@admin.register(Specification)
class SpecificationAdmin(admin.ModelAdmin):
    list_display = ['spec_type', 'name', 'value_nominal', 'unit', 'value_min', 'value_max', 'is_blocking', 'is_active', 'updated_at']
    list_filter = ['spec_type', 'is_blocking', 'is_active', 'created_at']
    search_fields = ['name', 'comments']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Identification', {
            'fields': ('spec_type', 'name', 'unit', 'is_active')
        }),
        ('Valeurs de Spécification', {
            'fields': ('value_min', 'value_min_alert', 'value_nominal', 'value_max_alert', 'value_max'),
            'description': 'Toutes les valeurs sont optionnelles. Ordre: min ≤ min_alerte ≤ nominale ≤ max_alerte ≤ max'
        }),
        ('Options', {
            'fields': ('is_blocking', 'max_nok'),
            'description': 'is_blocking: Le non-respect rend le produit non conforme. max_nok: Pour les épaisseurs uniquement.'
        }),
        ('Informations', {
            'fields': ('comments',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )