from django.contrib import admin
from .models import Operator, FabricationOrder


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    """Administration des opérateurs."""
    
    list_display = ['employee_id', 'first_name', 'last_name', 'training_completed', 'is_active']
    list_filter = ['is_active', 'training_completed']
    search_fields = ['first_name', 'last_name', 'employee_id']
    ordering = ['last_name', 'first_name']
    
    fieldsets = (
        ('Identification', {
            'fields': ('first_name', 'last_name', 'employee_id')
        }),
        ('Statut', {
            'fields': ('training_completed', 'is_active')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Édition
            return ['employee_id']
        return []


@admin.register(FabricationOrder)
class FabricationOrderAdmin(admin.ModelAdmin):
    """Administration des ordres de fabrication."""
    
    list_display = ['order_number', 'required_length', 'for_cutting', 'terminated', 'creation_date']
    list_filter = ['terminated', 'for_cutting', 'creation_date']
    search_fields = ['order_number']
    date_hierarchy = 'creation_date'
    ordering = ['-creation_date']
    
    fieldsets = (
        ('Identification', {
            'fields': ('order_number',)
        }),
        ('Production', {
            'fields': ('required_length', 'target_roll_length')
        }),
        ('Options', {
            'fields': ('for_cutting', 'terminated')
        }),
        ('Dates', {
            'fields': ('due_date',)
        }),
    )
    
    
    actions = ['mark_as_terminated', 'mark_as_active']
    
    def mark_as_terminated(self, request, queryset):
        """Action pour terminer des OF."""
        count = queryset.filter(terminated=False).update(terminated=True)
        if count:
            self.message_user(request, f"{count} OF terminé(s) avec succès.")
    mark_as_terminated.short_description = "Terminer les OF sélectionnés"
    
    def mark_as_active(self, request, queryset):
        """Action pour réactiver des OF."""
        count = queryset.filter(terminated=True).update(terminated=False)
        if count:
            self.message_user(request, f"{count} OF réactivé(s).")
    mark_as_active.short_description = "Réactiver les OF sélectionnés"