from django.contrib import admin
from .models import ChecklistTemplate, ChecklistItem, ChecklistResponse, MachineParametersHistory


class ChecklistItemInline(admin.TabularInline):
    """Inline pour gérer les items d'un template de check-list."""
    model = ChecklistItem
    extra = 1
    fields = ('order', 'text', 'is_required', 'is_active')
    ordering = ['order']


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    """Admin pour les templates de check-list."""
    list_display = ('name', 'is_active', 'is_default', 'item_count', 'created_at')
    list_filter = ('is_active', 'is_default')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ChecklistItemInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Configuration', {
            'fields': ('is_active', 'is_default')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def item_count(self, obj):
        """Nombre d'items dans le template."""
        return obj.items.count()
    item_count.short_description = "Nombre d'items"


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    """Admin pour les items de check-list."""
    list_display = ('text', 'template', 'order', 'is_required', 'is_active')
    list_filter = ('template', 'is_required', 'is_active')
    search_fields = ('text', 'template__name')
    list_editable = ('order', 'is_required', 'is_active')
    ordering = ['template', 'order']
    
    fieldsets = (
        (None, {
            'fields': ('template', 'text', 'order')
        }),
        ('Options', {
            'fields': ('is_required', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ChecklistResponse)
class ChecklistResponseAdmin(admin.ModelAdmin):
    """Admin pour les réponses de check-list."""
    list_display = ('shift', 'item_text', 'response', 'created_at')
    list_filter = ('response', 'shift__date', 'item__template')
    search_fields = ('shift__shift_id', 'item__text')
    readonly_fields = ('shift', 'item', 'response', 'created_at', 'updated_at')
    
    def item_text(self, obj):
        """Texte de l'item."""
        return obj.item.text
    item_text.short_description = "Item"
    
    def has_add_permission(self, request):
        """Les réponses sont créées via l'interface de production."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Les réponses sont en lecture seule."""
        return False


@admin.register(MachineParametersHistory)
class MachineParametersHistoryAdmin(admin.ModelAdmin):
    """Admin pour l'historique des paramètres machine."""
    list_display = ('timestamp', 'parameter_name', 'old_value', 'new_value', 'shift', 'modified_by')
    list_filter = ('parameter_type', 'timestamp', 'modified_by')
    search_fields = ('parameter_name', 'shift__shift_id', 'comment')
    readonly_fields = ('timestamp', 'shift', 'modified_by', 'parameter_name', 'parameter_type',
                      'old_value', 'new_value', 'machine_parameters', 'comment')
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Informations de modification', {
            'fields': ('timestamp', 'shift', 'modified_by')
        }),
        ('Paramètre modifié', {
            'fields': ('parameter_name', 'parameter_type', 'old_value', 'new_value')
        }),
        ('Contexte', {
            'fields': ('machine_parameters', 'comment')
        })
    )
    
    def has_add_permission(self, request):
        """L'historique est créé automatiquement."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """L'historique est en lecture seule."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Empêcher la suppression de l'historique."""
        return False