from django.contrib import admin
from .models import Shift, CurrentProd


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
            'fields': ('opening_time', 'availability_time', 'lost_time')
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
