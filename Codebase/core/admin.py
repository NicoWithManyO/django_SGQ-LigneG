from django.contrib import admin
from .models import Operator, FabricationOrder


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    """Configuration admin pour le modèle Operator."""
    
    list_display = ('last_name', 'first_name', 'employee_id', 'training_completed', 'is_active')
    list_filter = ('training_completed', 'is_active')
    search_fields = ('first_name', 'last_name', 'employee_id')
    list_editable = ('training_completed', 'is_active')
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'employee_id')
        }),
        ('Statut', {
            'fields': ('training_completed', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('employee_id', 'created_at', 'updated_at')


@admin.register(FabricationOrder)
class FabricationOrderAdmin(admin.ModelAdmin):
    """Configuration admin pour le modèle FabricationOrder."""
    
    list_display = ('order_number', 'required_length', 'target_roll_length', 'for_cutting', 'creation_date', 'due_date')
    list_filter = ('for_cutting', 'creation_date', 'due_date')
    search_fields = ('order_number',)
    list_editable = ('for_cutting',)
    
    fieldsets = (
        ('Identification', {
            'fields': ('order_number',)
        }),
        ('Quantités et dimensions', {
            'fields': ('required_length', 'target_roll_length')
        }),
        ('Options de production', {
            'fields': ('for_cutting',)
        }),
        ('Dates', {
            'fields': ('due_date', 'creation_date')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('creation_date', 'created_at', 'updated_at')
