from django.contrib import admin
from .models import Shift, CurrentProd, QualityControlSeries


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    """Configuration admin pour le modèle Shift."""
    
    list_display = ('shift_id', 'operator', 'date', 'vacation', 'total_length', 'ok_length')
    list_filter = ('vacation', 'date', 'operator')
    search_fields = ('shift_id', 'operator', 'operator_comments')
    readonly_fields = ('shift_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('shift_id', 'date', 'operator', 'vacation')
        }),
        ('Temps de production', {
            'fields': ('start_time', 'end_time', 'availability_time', 'lost_time')
        }),
        ('Longueurs (mètres)', {
            'fields': ('total_length', 'ok_length', 'nok_length', 'raw_waste_length')
        }),
        ('Paramètres machine', {
            'fields': ('started_at_beginning', 'meter_reading_start', 'started_at_end', 'meter_reading_end'),
            'classes': ('collapse',)
        }),
        ('Commentaires', {
            'fields': ('operator_comments',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Le shift_id devient readonly après création."""
        if obj:  # Modification d'un objet existant
            return self.readonly_fields
        return ('created_at', 'updated_at')  # Création d'un nouvel objet


@admin.register(CurrentProd)
class CurrentProdAdmin(admin.ModelAdmin):
    """Configuration admin pour le modèle CurrentProd."""
    
    list_display = ('session_key', 'updated_at', 'has_data')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('session_key',)
    readonly_fields = ('session_key', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Session', {
            'fields': ('session_key', 'created_at', 'updated_at')
        }),
        ('Données', {
            'fields': ('form_data',)
        }),
    )
    
    def has_data(self, obj):
        """Indique si l'objet contient des données."""
        return bool(obj.form_data and len(obj.form_data) > 0)
    has_data.boolean = True
    has_data.short_description = "Contient des données"


@admin.register(QualityControlSeries)
class QualityControlSeriesAdmin(admin.ModelAdmin):
    """Configuration admin pour le modèle QualityControlSeries."""
    
    list_display = ('__str__', 'shift', 'created_at', 'created_by', 'is_valid', 'has_micrometer', 'has_surface_mass', 'has_dry_extract')
    list_filter = ('created_at', 'created_by', 'loi_given', 'is_valid')
    search_fields = ('session_key', 'shift__shift_id')
    readonly_fields = ('created_at', 'micrometer_left_avg', 'micrometer_right_avg', 
                      'surface_mass_left_avg', 'surface_mass_right_avg')
    
    fieldsets = (
        ('Identification', {
            'fields': ('shift', 'session_key', 'created_by', 'is_valid')
        }),
        ('Contrôles Micronnaire', {
            'fields': (
                ('micrometer_left_1', 'micrometer_left_2', 'micrometer_left_3', 'micrometer_left_avg'),
                ('micrometer_right_1', 'micrometer_right_2', 'micrometer_right_3', 'micrometer_right_avg'),
            ),
            'classes': ('collapse',)
        }),
        ('Extrait Sec', {
            'fields': (('dry_extract', 'dry_extract_time'),),
            'classes': ('collapse',)
        }),
        ('Masses Surfaciques', {
            'fields': (
                ('surface_mass_gg', 'surface_mass_gc', 'surface_mass_left_avg'),
                ('surface_mass_dc', 'surface_mass_dd', 'surface_mass_right_avg'),
            ),
            'classes': ('collapse',)
        }),
        ('LOI', {
            'fields': (('loi_given', 'loi_time'),),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_micrometer(self, obj):
        """Indique si des mesures micronnaire sont présentes."""
        return any([obj.micrometer_left_1, obj.micrometer_left_2, obj.micrometer_left_3,
                   obj.micrometer_right_1, obj.micrometer_right_2, obj.micrometer_right_3])
    has_micrometer.boolean = True
    has_micrometer.short_description = "Micronnaire"
    
    def has_surface_mass(self, obj):
        """Indique si des mesures de masse surfacique sont présentes."""
        return any([obj.surface_mass_gg, obj.surface_mass_gc, 
                   obj.surface_mass_dc, obj.surface_mass_dd])
    has_surface_mass.boolean = True
    has_surface_mass.short_description = "Masse Surf."
    
    def has_dry_extract(self, obj):
        """Indique si l'extrait sec est renseigné."""
        return obj.dry_extract is not None
    has_dry_extract.boolean = True
    has_dry_extract.short_description = "Extrait Sec"
