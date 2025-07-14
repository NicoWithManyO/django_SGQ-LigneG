from django.contrib import admin
from .models import CurrentSession


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