from django.contrib import admin
from .models import Operator, FabricationOrder, Profile, Mode


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


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Configuration admin pour le modèle Profile."""
    
    list_display = ('name', 'machine_parameters', 'is_active', 'is_default')
    list_filter = ('is_active', 'is_default')
    search_fields = ('name',)
    list_editable = ('is_active', 'is_default')
    
    fieldsets = (
        ('Identification', {
            'fields': ('name',)
        }),
        ('Configuration', {
            'fields': ('machine_parameters', 'specifications')
        }),
        ('État', {
            'fields': ('is_active', 'is_default')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('specifications',)
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(FabricationOrder)
class FabricationOrderAdmin(admin.ModelAdmin):
    """Configuration admin pour le modèle FabricationOrder."""
    
    list_display = ('order_number', 'profile', 'required_length', 'target_roll_length', 'for_cutting', 'creation_date', 'due_date')
    list_filter = ('for_cutting', 'creation_date', 'due_date')
    search_fields = ('order_number',)
    list_editable = ('for_cutting',)
    
    fieldsets = (
        ('Identification', {
            'fields': ('order_number', 'profile')
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


@admin.register(Mode)
class ModeAdmin(admin.ModelAdmin):
    """Configuration admin pour le modèle Mode."""
    
    list_display = ('name', 'code', 'is_enabled', 'is_active', 'updated_at')
    list_filter = ('is_enabled', 'is_active')
    search_fields = ('name', 'code', 'description')
    list_editable = ('is_enabled',)
    prepopulated_fields = {'code': ('name',)}
    
    fieldsets = (
        ('Identification', {
            'fields': ('name', 'code', 'description')
        }),
        ('État', {
            'fields': ('is_enabled', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
