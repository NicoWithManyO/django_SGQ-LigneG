from django.contrib import admin
from .models import CurrentSession, LiveRoll


@admin.register(CurrentSession)
class CurrentSessionAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'get_operator_name', 'get_date', 'get_vacation', 'updated_at')
    list_filter = ('updated_at', 'created_at')
    search_fields = ('session_key',)
    date_hierarchy = 'updated_at'
    readonly_fields = ('created_at', 'updated_at', 'formatted_session_data')
    
    fieldsets = (
        ('Session', {
            'fields': ('session_key',)
        }),
        ('Données de session', {
            'fields': ('session_data', 'formatted_session_data')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_operator_name(self, obj):
        # Le champ est stocké comme 'operator' (pas 'operator_name')
        operator_value = obj.session_data.get('operator', 'Sans opérateur')
        
        # Si la valeur ressemble à un ID (nombre), essayer de récupérer le nom
        if operator_value and str(operator_value).isdigit():
            try:
                from core.models import Operator
                operator_obj = Operator.objects.get(pk=int(operator_value))
                return operator_obj.full_name
            except:
                return f"Opérateur #{operator_value}"
        else:
            return operator_value or 'Sans opérateur'
    get_operator_name.short_description = 'Opérateur'
    
    def get_date(self, obj):
        return obj.session_data.get('date', 'Sans date')
    get_date.short_description = 'Date'
    
    def get_vacation(self, obj):
        return obj.session_data.get('vacation', 'Sans vacation')
    get_vacation.short_description = 'Vacation'
    
    def formatted_session_data(self, obj):
        import json
        return json.dumps(obj.session_data, indent=2, ensure_ascii=False)
    formatted_session_data.short_description = 'Données formatées'


@admin.register(LiveRoll)
class LiveRollAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'get_roll_id', 'get_status', 'get_compliant', 'updated_at')
    list_filter = ('is_active', 'updated_at', 'created_at')
    search_fields = ('session_key',)
    date_hierarchy = 'updated_at'
    readonly_fields = ('created_at', 'updated_at', 'formatted_roll_data')
    
    fieldsets = (
        ('Session', {
            'fields': ('session_key', 'is_active')
        }),
        ('Données du rouleau', {
            'fields': ('roll_data', 'formatted_roll_data')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_roll_id(self, obj):
        return obj.roll_data.get('roll_id', 'Sans ID')
    get_roll_id.short_description = 'ID Rouleau'
    
    def get_status(self, obj):
        return "Actif" if obj.is_active else "Archivé"
    get_status.short_description = 'Statut'
    
    def get_compliant(self, obj):
        is_compliant = obj.roll_data.get('is_compliant', None)
        if is_compliant is None:
            return '-'
        return '✓ Conforme' if is_compliant else '✗ Non conforme'
    get_compliant.short_description = 'Conformité'
    
    def formatted_roll_data(self, obj):
        import json
        return json.dumps(obj.roll_data, indent=2, ensure_ascii=False)
    formatted_roll_data.short_description = 'Données formatées'