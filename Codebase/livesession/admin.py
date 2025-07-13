from django.contrib import admin
from .models import CurrentProductionState, LiveShift


@admin.register(CurrentProductionState)
class CurrentProductionStateAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'user', 'current_of', 'cutting_of', 'target_length', 'updated_at')
    list_filter = ('updated_at', 'created_at')
    search_fields = ('session_key', 'user__username', 'current_of__of_number')
    date_hierarchy = 'updated_at'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Session', {
            'fields': ('session_key', 'user')
        }),
        ('OF actifs', {
            'fields': ('current_of', 'cutting_of', 'target_length')
        }),
        ('Configuration', {
            'fields': ('selected_profile', 'active_modes')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(LiveShift)
class LiveShiftAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'get_operator_name', 'get_date', 'get_vacation', 'updated_at')
    list_filter = ('updated_at', 'created_at')
    search_fields = ('session_key',)
    date_hierarchy = 'updated_at'
    readonly_fields = ('created_at', 'updated_at', 'formatted_shift_data')
    
    fieldsets = (
        ('Session', {
            'fields': ('session_key',)
        }),
        ('Données du poste', {
            'fields': ('shift_data', 'formatted_shift_data')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_operator_name(self, obj):
        return obj.shift_data.get('operator_name', 'Sans opérateur')
    get_operator_name.short_description = 'Opérateur'
    
    def get_date(self, obj):
        return obj.shift_data.get('date', 'Sans date')
    get_date.short_description = 'Date'
    
    def get_vacation(self, obj):
        return obj.shift_data.get('vacation', 'Sans vacation')
    get_vacation.short_description = 'Vacation'
    
    def formatted_shift_data(self, obj):
        import json
        return json.dumps(obj.shift_data, indent=2, ensure_ascii=False)
    formatted_shift_data.short_description = 'Données formatées'