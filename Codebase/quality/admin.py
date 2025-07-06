from django.contrib import admin
from .models import DefectType, RollDefect, ThicknessMeasurement, ThicknessSpecification

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


@admin.register(ThicknessSpecification)
class ThicknessSpecificationAdmin(admin.ModelAdmin):
    list_display = ['ep_nominale', 'ep_mini', 'ep_mini_alerte', 'ep_max_alerte', 'is_active', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['comments']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Spécifications d\'Épaisseur', {
            'fields': ('ep_mini', 'ep_mini_alerte', 'ep_nominale', 'ep_max_alerte', 'is_active'),
            'description': 'Ordre: mini ≤ mini_alerte ≤ nominale ≤ max_alerte'
        }),
        ('Informations', {
            'fields': ('comments',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
