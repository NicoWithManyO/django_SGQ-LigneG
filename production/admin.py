from django.contrib import admin
from django.utils.html import format_html
from .models import Shift, Roll, CurrentProfile
from quality.models import RollThickness, RollDefect


class RollInline(admin.TabularInline):
    """Inline pour afficher les rouleaux d'un poste."""
    model = Roll
    extra = 0
    fields = ['roll_id', 'fabrication_order', 'length', 'grammage_calc', 'status', 'destination', 'preshipper_assigned']
    readonly_fields = ['roll_id', 'grammage_calc', 'preshipper_assigned']
    ordering = ['-created_at']
    classes = ['collapse']  # Dépliable par défaut
    
    def has_add_permission(self, request, obj=None):
        """Désactive l'ajout via l'admin."""
        return False


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    """Administration des postes de production."""
    
    list_display = ['shift_id', 'date', 'vacation', 'operator', 
                    'get_total_length', 'availability_time', 'checklist_signed', 'is_training_display']
    list_filter = ['vacation', 'date', 'checklist_signed', 'started_at_beginning', 'started_at_end', 'is_training_shift']
    search_fields = ['shift_id', 'operator__first_name', 'operator__last_name']
    date_hierarchy = 'date'
    ordering = ['-date', 'vacation']
    
    fieldsets = (
        ('Identification', {
            'fields': ('date', 'operator', 'vacation')
        }),
        ('Horaires', {
            'fields': ('start_time', 'end_time', 'availability_time', 'lost_time')
        }),
        ('Production (depuis TRS)', {
            'fields': ('get_total_length', 'get_ok_length', 'get_nok_length', 'get_raw_waste_length'),
            'description': 'Les données de production sont maintenant stockées dans le modèle TRS'
        }),
        ('Moyennes du poste', {
            'fields': ('avg_thickness_left_shift', 'avg_thickness_right_shift', 'avg_grammage_shift'),
            'classes': ('collapse',)
        }),
        ('État machine', {
            'fields': (
                ('started_at_beginning', 'meter_reading_start'),
                ('started_at_end', 'meter_reading_end')
            ),
            'classes': ('collapse',)
        }),
        ('Check-list', {
            'fields': ('checklist_signed', 'checklist_signed_time')
        }),
        ('Formation', {
            'fields': ('is_training_shift', 'trainee'),
            'classes': ('collapse',)
        }),
        ('Commentaires', {
            'fields': ('operator_comments',),
            'classes': ('wide',)
        }),
    )
    
    readonly_fields = ['shift_id', 'availability_time', 'lost_time', 'get_total_length', 
                      'get_ok_length', 'get_nok_length', 'get_raw_waste_length',
                      'avg_thickness_left_shift', 'avg_thickness_right_shift', 'avg_grammage_shift']
    
    inlines = [RollInline]  # Afficher les rouleaux du poste
    
    def get_total_length(self, obj):
        """Longueur totale depuis TRS."""
        return f"{obj.total_length} m"
    get_total_length.short_description = "Longueur totale"
    
    def get_ok_length(self, obj):
        """Longueur OK depuis TRS."""
        return f"{obj.ok_length} m"
    get_ok_length.short_description = "Longueur conforme"
    
    def get_nok_length(self, obj):
        """Longueur NOK depuis TRS."""
        return f"{obj.nok_length} m"
    get_nok_length.short_description = "Longueur non conforme"
    
    def get_raw_waste_length(self, obj):
        """Déchet brut depuis TRS."""
        return f"{obj.raw_waste_length} m"
    get_raw_waste_length.short_description = "Déchet brut"
    
    def is_training_display(self, obj):
        """Affiche si c'est un poste de formation."""
        if obj.is_training_shift and obj.trainee:
            return format_html('<span style="color: #007bff; font-weight: bold;">👥 {}</span>', 
                              obj.trainee.full_name)
        elif obj.is_training_shift:
            return format_html('<span style="color: #ffc107;">👥 Formation</span>')
        return ""
    is_training_display.short_description = "Formation"


class RollThicknessInline(admin.TabularInline):
    """Inline pour afficher les épaisseurs d'un rouleau."""
    model = RollThickness
    extra = 0
    fields = ['meter_position', 'measurement_point', 'thickness_value', 'is_catchup', 'is_within_tolerance', 'created_at']
    readonly_fields = ['meter_position', 'measurement_point', 'thickness_value', 'is_catchup', 'is_within_tolerance', 'created_at']
    ordering = ['meter_position', 'measurement_point']
    classes = ['collapse']  # Dépliable par défaut
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        """Désactive l'ajout via l'admin."""
        return False


class RollDefectInline(admin.TabularInline):
    """Inline pour afficher les défauts d'un rouleau."""
    model = RollDefect
    extra = 0
    fields = ['defect_type', 'meter_position', 'side_position', 'created_at']
    readonly_fields = ['defect_type', 'meter_position', 'side_position', 'created_at']
    ordering = ['-created_at']
    classes = ['collapse']  # Dépliable par défaut
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        """Désactive l'ajout via l'admin."""
        return False


@admin.register(Roll)
class RollAdmin(admin.ModelAdmin):
    """Administration des rouleaux."""
    
    list_display = ['roll_id', 'shift', 'fabrication_order', 'length', 'grammage_display',
                    'status_display', 'destination', 'preshipper_display', 'has_defects', 'created_at']
    list_filter = ['status', 'destination', 'has_blocking_defects', 'has_thickness_issues', 
                   'preshipper_assigned', 'created_at', 'fabrication_order']
    search_fields = ['roll_id', 'shift__shift_id', 'fabrication_order__order_number']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Identification', {
            'fields': ('roll_id', 'shift', 'fabrication_order', 'roll_number')
        }),
        ('Données de production', {
            'fields': ('length', 'tube_mass', 'total_mass', 'net_mass', 'grammage_calc')
        }),
        ('Statut et destination', {
            'fields': ('status', 'destination', 'has_blocking_defects', 'has_thickness_issues')
        }),
        ('Épaisseurs moyennes', {
            'fields': ('avg_thickness_left', 'avg_thickness_right'),
            'classes': ('collapse',)
        }),
        ('Traçabilité', {
            'fields': ('shift_id_str', 'session_key'),
            'classes': ('collapse',)
        }),
        ('Pré-shipper', {
            'fields': ('preshipper_assigned', 'preshipper_assigned_at'),
            'classes': ('collapse',)
        }),
        ('Commentaire', {
            'fields': ('comment',),
            'classes': ('wide',)
        }),
    )
    
    readonly_fields = ['roll_id', 'net_mass', 'grammage_calc', 'preshipper_assigned_at']
    
    inlines = [RollThicknessInline, RollDefectInline]
    
    def status_display(self, obj):
        """Affiche le statut avec couleur."""
        if obj.status == 'CONFORME':
            color = 'green'
            icon = '✓'
        else:
            color = 'red'
            icon = '✗'
        return format_html('<span style="color: {};">{} {}</span>', 
                          color, icon, obj.get_status_display())
    status_display.short_description = "Statut"
    
    def grammage_display(self, obj):
        """Affiche le grammage."""
        if obj.grammage_calc:
            return f"{obj.grammage_calc} g/m"
        return "-"
    grammage_display.short_description = "Grammage"
    
    def has_defects(self, obj):
        """Indique si le rouleau a des défauts."""
        return obj.defects.exists()
    has_defects.boolean = True
    has_defects.short_description = "Défauts"
    
    def preshipper_display(self, obj):
        """Affiche le pré-shipper assigné."""
        if obj.preshipper_assigned:
            date_str = obj.preshipper_assigned_at.strftime('%d/%m %H:%M') if obj.preshipper_assigned_at else ''
            return format_html('<span style="color: #e83e8c; font-weight: bold;">{}</span><br/><small style="color: #6c757d;">{}</small>', 
                              obj.preshipper_assigned, date_str)
        return format_html('<span style="color: #28a745;">✓ Disponible</span>')
    preshipper_display.short_description = "Pré-shipper"
    
    actions = ['force_to_cutting', 'set_as_conform', 'release_from_preshipper']
    
    def force_to_cutting(self, request, queryset):
        """Force les rouleaux sélectionnés vers la découpe."""
        count = queryset.filter(status='CONFORME').update(destination='DECOUPE_FORCEE')
        if count:
            self.message_user(request, f"{count} rouleau(x) forcé(s) vers la découpe.")
    force_to_cutting.short_description = "Forcer vers la découpe"
    
    def set_as_conform(self, request, queryset):
        """Marque les rouleaux comme conformes."""
        count = queryset.update(status='CONFORME', destination='PRODUCTION',
                               has_blocking_defects=False, has_thickness_issues=False)
        if count:
            self.message_user(request, f"{count} rouleau(x) marqué(s) conforme(s).")
    set_as_conform.short_description = "Marquer comme conforme"
    
    def release_from_preshipper(self, request, queryset):
        """Libère les rouleaux du pré-shipper pour les rendre disponibles."""
        count = queryset.filter(preshipper_assigned__isnull=False).update(
            preshipper_assigned=None, 
            preshipper_assigned_at=None
        )
        if count:
            self.message_user(request, f"{count} rouleau(x) libéré(s) du pré-shipper.")
    release_from_preshipper.short_description = "Libérer du pré-shipper"


@admin.register(CurrentProfile)
class CurrentProfileAdmin(admin.ModelAdmin):
    """Administration du profil actuel."""
    
    list_display = ['profile', 'selected_at']
    fields = ['profile', 'selected_at']
    readonly_fields = ['selected_at']
    
    def has_add_permission(self, request):
        """Un seul profil actuel peut exister."""
        return not CurrentProfile.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Empêche la suppression."""
        return False