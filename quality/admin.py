from django.contrib import admin
from django.utils.html import format_html
from .models import RollDefect, RollThickness, Controls


@admin.register(RollDefect)
class RollDefectAdmin(admin.ModelAdmin):
    """Administration des défauts sur rouleaux."""
    
    list_display = ['roll', 'defect_type', 'meter_position', 'side_position', 'created_at']
    list_filter = ['defect_type', 'side_position', 'created_at']
    search_fields = ['roll__roll_id', 'defect_type__name', 'comment']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Identification', {
            'fields': ('roll', 'defect_type')
        }),
        ('Position', {
            'fields': ('meter_position', 'side_position')
        }),
        ('Détails', {
            'fields': ('comment',),
            'classes': ('wide',)
        }),
    )
    
    autocomplete_fields = ['roll']


@admin.register(RollThickness)
class RollThicknessAdmin(admin.ModelAdmin):
    """Administration des mesures d'épaisseur."""
    
    list_display = ['roll', 'meter_position', 'measurement_point', 'thickness_value', 
                    'tolerance_display', 'catchup_display', 'created_at']
    list_filter = ['measurement_point', 'is_within_tolerance', 'is_catchup', 'created_at']
    search_fields = ['roll__roll_id']
    date_hierarchy = 'created_at'
    ordering = ['roll', 'meter_position', 'measurement_point']
    
    fieldsets = (
        ('Identification', {
            'fields': ('roll',)
        }),
        ('Mesure', {
            'fields': ('meter_position', 'measurement_point', 'thickness_value')
        }),
        ('Validation', {
            'fields': ('is_catchup', 'is_within_tolerance')
        }),
    )
    
    autocomplete_fields = ['roll']
    
    def tolerance_display(self, obj):
        """Affiche l'état de tolérance."""
        if obj.is_within_tolerance:
            return format_html('<span style="color: green;">✓ OK</span>')
        else:
            return format_html('<span style="color: red;">✗ NOK</span>')
    tolerance_display.short_description = "Tolérance"
    
    def catchup_display(self, obj):
        """Affiche si c'est un rattrapage."""
        if obj.is_catchup:
            return format_html('<span style="color: orange; font-weight: bold;">⚡ Rattrapage</span>')
        else:
            return format_html('<span style="color: #666;">—</span>')
    catchup_display.short_description = "Rattrapage"


@admin.register(Controls)
class ControlsAdmin(admin.ModelAdmin):
    """Administration des contrôles qualité."""
    
    list_display = ['shift_display', 'created_at', 'validation_display', 
                    'loi_given', 'created_by']
    list_filter = ['is_valid', 'loi_given', 'created_at']
    search_fields = ['shift__shift_id', 'session_key']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Identification', {
            'fields': ('shift', 'session_key', 'created_by')
        }),
        ('Contrôles Micronnaire', {
            'fields': (
                ('micrometer_left_1', 'micrometer_left_2', 'micrometer_left_3', 'micrometer_left_avg'),
                ('micrometer_right_1', 'micrometer_right_2', 'micrometer_right_3', 'micrometer_right_avg')
            ),
            'classes': ('wide',)
        }),
        ('Masses Surfaciques', {
            'fields': (
                ('surface_mass_gg', 'surface_mass_gc', 'surface_mass_left_avg'),
                ('surface_mass_dc', 'surface_mass_dd', 'surface_mass_right_avg')
            ),
            'classes': ('wide',)
        }),
        ('Autres contrôles', {
            'fields': (
                ('dry_extract', 'dry_extract_time'),
                ('loi_given', 'loi_time')
            )
        }),
        ('Validation', {
            'fields': ('is_valid',)
        }),
    )
    
    readonly_fields = ['micrometer_left_avg', 'micrometer_right_avg', 
                      'surface_mass_left_avg', 'surface_mass_right_avg']
    
    def shift_display(self, obj):
        """Affiche le shift ou la session."""
        if obj.shift:
            return obj.shift.shift_id
        return f"Session {obj.session_key[:8]}..."
    shift_display.short_description = "Poste/Session"
    
    def validation_display(self, obj):
        """Affiche l'état de validation."""
        if obj.is_valid:
            return format_html('<span style="color: green;">✓ Valide</span>')
        else:
            return format_html('<span style="color: red;">✗ Non valide</span>')
    validation_display.short_description = "Validation"