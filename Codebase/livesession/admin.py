from django.contrib import admin
from .models import CurrentProductionState, LiveShift, LiveRoll, LiveQualityControl


@admin.register(CurrentProductionState)
class CurrentProductionStateAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'user', 'current_of', 'cutting_of', 'target_length', 'roll_number', 'updated_at')
    list_filter = ('updated_at', 'created_at')
    search_fields = ('session_key', 'user__username', 'current_of__of_number')
    date_hierarchy = 'updated_at'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Session', {
            'fields': ('session_key', 'user')
        }),
        ('OF actifs', {
            'fields': ('current_of', 'cutting_of', 'target_length', 'roll_number')
        }),
        ('Configuration', {
            'fields': ('selected_profile', 'active_modes', 'active_productivity_tab')
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
        # Le champ est stocké comme 'operator' (pas 'operator_name')
        operator_value = obj.shift_data.get('operator', 'Sans opérateur')
        
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
        return obj.shift_data.get('date', 'Sans date')
    get_date.short_description = 'Date'
    
    def get_vacation(self, obj):
        return obj.shift_data.get('vacation', 'Sans vacation')
    get_vacation.short_description = 'Vacation'
    
    def formatted_shift_data(self, obj):
        import json
        return json.dumps(obj.shift_data, indent=2, ensure_ascii=False)
    formatted_shift_data.short_description = 'Données formatées'


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


@admin.register(LiveQualityControl)
class LiveQualityControlAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'get_micronnaire_count', 'get_surface_mass_count', 'get_extrait_sec', 'get_loi_status', 'updated_at')
    list_filter = ('updated_at', 'created_at')
    search_fields = ('session_key',)
    date_hierarchy = 'updated_at'
    readonly_fields = ('created_at', 'updated_at', 'formatted_quality_data')
    
    fieldsets = (
        ('Session', {
            'fields': ('session_key',)
        }),
        ('Données qualité', {
            'fields': ('quality_data', 'formatted_quality_data')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_micronnaire_count(self, obj):
        data = obj.quality_data
        left = data.get('micronnaire_left', [])
        right = data.get('micronnaire_right', [])
        count = len([v for v in left + right if v is not None])
        return f"{count}/6"
    get_micronnaire_count.short_description = 'Micronnaires'
    
    def get_surface_mass_count(self, obj):
        data = obj.quality_data
        fields = ['surface_mass_gg', 'surface_mass_gc', 'surface_mass_dc', 'surface_mass_dd']
        count = len([f for f in fields if data.get(f) is not None])
        return f"{count}/4"
    get_surface_mass_count.short_description = 'Masses surf.'
    
    def get_extrait_sec(self, obj):
        value = obj.quality_data.get('extrait_sec')
        time = obj.quality_data.get('extrait_sec_time', '')
        if value is not None:
            return f"{value}% à {time}" if time else f"{value}%"
        return '-'
    get_extrait_sec.short_description = 'Extrait sec'
    
    def get_loi_status(self, obj):
        loi_given = obj.quality_data.get('loi_given', False)
        time = obj.quality_data.get('loi_time', '')
        if loi_given:
            return f"✓ Donné à {time}" if time else "✓ Donné"
        return '-'
    get_loi_status.short_description = 'LOI'
    
    def formatted_quality_data(self, obj):
        import json
        return json.dumps(obj.quality_data, indent=2, ensure_ascii=False)
    formatted_quality_data.short_description = 'Données formatées'