from django.contrib import admin
from .models import Shift, QualityControl, Roll, RollDefect, RollThickness, LostTimeEntry, MachineParameters
from core.admin_filters import RelatedCountedFilter, BooleanCountedFilter, ChoiceCountedFilter


class LostTimeInline(admin.TabularInline):
    """Inline pour les temps d'arrêt d'un shift."""
    model = LostTimeEntry
    extra = 0
    fields = ('motif', 'comment', 'duration', 'created_at')
    readonly_fields = ('motif', 'comment', 'duration', 'created_at')
    can_delete = True
    
    def has_add_permission(self, request, obj=None):
        return False


# Filtre personnalisé pour vacation avec comptage
class VacationCountedFilter(admin.SimpleListFilter):
    title = 'vacation'
    parameter_name = 'vacation'
    
    def lookups(self, request, model_admin):
        queryset = model_admin.get_queryset(request)
        choices = []
        
        for vacation, label in [('Matin', 'Matin'), ('ApresMidi', 'Après-midi'), ('Nuit', 'Nuit'), ('Journee', 'Journée')]:
            count = queryset.filter(vacation=vacation).count()
            if count > 0:
                choices.append((vacation, f'{label} ({count})'))
        
        return choices
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(vacation=self.value())
        return queryset


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    """Configuration admin pour le modèle Shift."""
    
    list_display = ('shift_id', 'operator', 'date', 'vacation', 'total_length', 'ok_length')
    list_filter = (VacationCountedFilter, 'date', ('operator', RelatedCountedFilter))
    search_fields = ('shift_id', 'operator__first_name', 'operator__last_name', 'operator_comments')
    readonly_fields = ('shift_id', 'checklist_signed', 'checklist_signed_time', 'created_at', 'updated_at')
    inlines = [LostTimeInline]
    
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
        ('Check-list', {
            'fields': ('checklist_signed', 'checklist_signed_time'),
            'classes': ('collapse',)
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
    
    def delete_queryset(self, request, queryset):
        """Suppression personnalisée pour éviter les erreurs avec les signaux."""
        # Désactiver temporairement les signaux lors de la suppression en masse
        from django.db.models import signals
        from production.signals import update_shift_lost_time
        
        # Déconnecter le signal
        signals.post_delete.disconnect(update_shift_lost_time, sender=LostTimeEntry)
        
        try:
            # Effectuer la suppression
            super().delete_queryset(request, queryset)
        finally:
            # Reconnecter le signal
            signals.post_delete.connect(update_shift_lost_time, sender=LostTimeEntry)


@admin.register(QualityControl)
class QualityControlAdmin(admin.ModelAdmin):
    """Configuration admin pour le modèle QualityControl."""
    
    list_display = ('__str__', 'shift', 'created_at', 'created_by', 'is_valid', 'has_micrometer', 'has_surface_mass', 'has_dry_extract')
    list_filter = ('created_at', 'created_by', 'loi_given', 'is_valid')
    search_fields = ('session_key', 'shift__shift_id')
    readonly_fields = ('shift', 'session_key', 'created_by', 'is_valid', 'created_at',
                      'micrometer_left_1', 'micrometer_left_2', 'micrometer_left_3', 'micrometer_left_avg',
                      'micrometer_right_1', 'micrometer_right_2', 'micrometer_right_3', 'micrometer_right_avg',
                      'dry_extract', 'dry_extract_time',
                      'surface_mass_gg', 'surface_mass_gc', 'surface_mass_left_avg',
                      'surface_mass_dc', 'surface_mass_dd', 'surface_mass_right_avg',
                      'loi_given', 'loi_time')
    
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
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Permettre la suppression si c'est via la suppression en cascade d'un rouleau
        return True


class RollDefectInline(admin.TabularInline):
    """Inline pour les défauts d'un rouleau."""
    model = RollDefect
    extra = 0
    fields = ('defect_name', 'meter_position', 'side_position')
    readonly_fields = ('defect_name', 'meter_position', 'side_position')
    can_delete = True
    
    def has_add_permission(self, request, obj=None):
        return False


class RollThicknessInline(admin.TabularInline):
    """Inline pour les mesures d'épaisseur d'un rouleau."""
    model = RollThickness
    extra = 0
    fields = ('meter_position', 'measurement_point', 'thickness_value', 
              'is_catchup', 'is_within_tolerance')
    readonly_fields = ('meter_position', 'measurement_point', 'thickness_value', 
                      'is_catchup', 'is_within_tolerance')
    can_delete = True
    classes = ['collapse']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Roll)
class RollAdmin(admin.ModelAdmin):
    """Configuration admin pour le modèle Roll."""
    
    list_display = ('roll_id', 'shift', 'get_operator', 'roll_number', 'length', 'status', 
                    'destination')
    list_filter = ('status', 'destination', 'has_blocking_defects', 'has_thickness_issues', 'shift__operator', 'shift')
    search_fields = ('roll_id', 'shift__shift_id', 'shift__operator__first_name', 'shift__operator__last_name')
    readonly_fields = ('created_at', 'updated_at', 'shift_id_str', 'length', 'tube_mass', 'total_mass', 'net_mass', 'avg_thickness_left', 'avg_thickness_right')
    inlines = [RollDefectInline, RollThicknessInline]
    
    fieldsets = (
        ('Identification', {
            'fields': ('roll_id', 'shift', 'shift_id_str', 'fabrication_order', 'roll_number')
        }),
        ('Données de production', {
            'fields': ('length', 'tube_mass', 'total_mass', 'net_mass')
        }),
        ('Moyennes d\'épaisseur', {
            'fields': ('avg_thickness_left', 'avg_thickness_right'),
            'classes': ('collapse',)
        }),
        ('Conformité', {
            'fields': ('status', 'destination', 'has_blocking_defects', 'has_thickness_issues')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_operator(self, obj):
        """Retourne l'opérateur du shift associé."""
        if obj.shift and obj.shift.operator:
            return obj.shift.operator
        return '-'
    get_operator.short_description = 'Opérateur'
    get_operator.admin_order_field = 'shift__operator'


@admin.register(RollDefect)
class RollDefectAdmin(admin.ModelAdmin):
    """Configuration admin pour le modèle RollDefect."""
    
    list_display = ('roll', 'defect_name', 'meter_position', 'side_position', 'created_at')
    list_filter = ('defect_name', 'side_position', 'created_at')
    search_fields = ('roll__roll_id', 'defect_name')
    readonly_fields = ('roll', 'defect_name', 'meter_position', 'side_position', 'created_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Permettre la suppression si c'est via la suppression en cascade d'un rouleau
        return True
    
    fieldsets = (
        ('Rouleau', {
            'fields': ('roll',)
        }),
        ('Défaut', {
            'fields': ('defect_name', 'meter_position', 'side_position')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(RollThickness)
class RollThicknessAdmin(admin.ModelAdmin):
    """Configuration admin pour le modèle RollThickness."""
    
    list_display = ('roll', 'meter_position', 'measurement_point', 'thickness_value', 
                    'is_catchup', 'is_within_tolerance', 'created_at')
    list_filter = ('is_within_tolerance', 'is_catchup', 'measurement_point', 'created_at')
    search_fields = ('roll__roll_id',)
    readonly_fields = ('roll', 'meter_position', 'measurement_point', 'thickness_value', 
                      'is_catchup', 'is_within_tolerance', 'created_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Permettre la suppression si c'est via la suppression en cascade d'un rouleau
        return True
    
    fieldsets = (
        ('Rouleau', {
            'fields': ('roll',)
        }),
        ('Mesure', {
            'fields': ('meter_position', 'measurement_point', 'thickness_value', 'is_catchup')
        }),
        ('Validation', {
            'fields': ('is_within_tolerance',)
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(LostTimeEntry)
class LostTimeEntryAdmin(admin.ModelAdmin):
    """Configuration admin pour le modèle LostTimeEntry."""
    
    list_display = ('shift', 'motif', 'duration', 'comment', 'created_at')
    list_filter = ('motif', 'created_at', 'shift')
    search_fields = ('shift__shift_id', 'motif', 'comment')
    readonly_fields = ('shift', 'session_key', 'motif', 'comment', 'duration', 'created_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Permettre la suppression si c'est via la suppression en cascade d'un rouleau
        return True
    
    fieldsets = (
        ('Shift', {
            'fields': ('shift', 'session_key')
        }),
        ('Temps d\'arrêt', {
            'fields': ('motif', 'comment', 'duration')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(MachineParameters)
class MachineParametersAdmin(admin.ModelAdmin):
    """Configuration admin pour le modèle MachineParameters."""
    
    list_display = ('name', 'is_active', 'oxygen_primary', 'oxygen_secondary', 
                    'propane_primary', 'propane_secondary', 'belt_speed', 'get_belt_speed_m_min', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at', 'get_belt_speed_m_min_detail')
    
    fieldsets = (
        ('Identification', {
            'fields': ('name', 'is_active')
        }),
        ('Paramètres FIBRAGE', {
            'fields': (
                ('oxygen_primary', 'oxygen_secondary'),
                ('propane_primary', 'propane_secondary'),
                ('speed_primary', 'speed_secondary'),
            ),
            'description': 'Paramètres de la machine de fibrage'
        }),
        ('Paramètres ENSIMEUSE', {
            'fields': ('belt_speed', 'get_belt_speed_m_min_detail'),
            'description': 'Paramètres de l\'ensimeuse'
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_belt_speed_m_min(self, obj):
        """Affiche la vitesse du tapis en m/min."""
        if obj.belt_speed_m_per_minute:
            return f"{obj.belt_speed_m_per_minute} m/min"
        return "-"
    get_belt_speed_m_min.short_description = "Vitesse tapis (m/min)"
    
    def get_belt_speed_m_min_detail(self, obj):
        """Affiche la conversion détaillée de la vitesse."""
        if obj.belt_speed:
            return f"{obj.belt_speed} m/h = {obj.belt_speed_m_per_minute} m/min"
        return "-"
    get_belt_speed_m_min_detail.short_description = "Conversion vitesse"
    
    def save_model(self, request, obj, form, change):
        """Assurer qu'un seul profil est actif à la fois si nécessaire."""
        if obj.is_active:
            # Optionnel : désactiver les autres profils si on veut un seul actif
            # MachineParameters.objects.exclude(pk=obj.pk).update(is_active=False)
            pass
        super().save_model(request, obj, form, change)