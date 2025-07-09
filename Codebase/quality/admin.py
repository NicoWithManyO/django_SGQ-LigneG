from django.contrib import admin
from .models import DefectType, RollDefect, ThicknessMeasurement, Specification

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


@admin.register(RollDefect)
class RollDefectAdmin(admin.ModelAdmin):
    list_display = ['roll_id', 'defect_type', 'meter_position', 'side_position', 'status', 'is_blocking', 'detected_at']
    list_filter = ['status', 'is_blocking', 'side_position', 'defect_type']
    search_fields = ['roll_id', 'description']
    readonly_fields = ['detected_at', 'is_blocking']
    
    fieldsets = (
        ('Identification', {
            'fields': ('roll_id', 'defect_type')
        }),
        ('Localisation', {
            'fields': ('meter_position', 'side_position')
        }),
        ('Défaut', {
            'fields': ('description', 'operator_comments')
        }),
        ('Statut', {
            'fields': ('status', 'is_blocking', 'resolved_at')
        }),
        ('Métadonnées', {
            'fields': ('detected_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ThicknessMeasurement)
class ThicknessMeasurementAdmin(admin.ModelAdmin):
    list_display = ['roll_id', 'meter_position', 'measurement_point', 'thickness_value', 'is_within_tolerance', 'measured_at']
    list_filter = ['measurement_point', 'is_within_tolerance']
    search_fields = ['roll_id']
    readonly_fields = ['measured_at', 'is_within_tolerance']
    
    fieldsets = (
        ('Identification', {
            'fields': ('roll_id',)
        }),
        ('Mesure', {
            'fields': ('meter_position', 'measurement_point', 'thickness_value')
        }),
        ('Tolérances', {
            'fields': ('min_tolerance', 'max_tolerance', 'is_within_tolerance')
        }),
        ('Commentaires', {
            'fields': ('operator_comments',)
        }),
        ('Métadonnées', {
            'fields': ('measured_at',),
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