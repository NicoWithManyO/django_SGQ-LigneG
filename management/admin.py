from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline pour éditer le profil utilisateur directement dans la page User."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil'
    fields = ['default_visa']
    
    def get_queryset(self, request):
        """Surcharge pour créer automatiquement le profil s'il n'existe pas."""
        qs = super().get_queryset(request)
        return qs
    
    def has_add_permission(self, request, obj=None):
        """Un seul profil par utilisateur."""
        return False


# Désenregistrer l'admin User par défaut
admin.site.unregister(User)


# Créer une nouvelle classe UserAdmin étendue
class ExtendedUserAdmin(UserAdmin):
    """Admin User étendu avec le profil."""
    inlines = [UserProfileInline]
    
    def save_model(self, request, obj, form, change):
        """S'assurer qu'un profil existe lors de la sauvegarde."""
        super().save_model(request, obj, form, change)
        # Créer le profil s'il n'existe pas
        UserProfile.objects.get_or_create(user=obj)
    
    def save_formset(self, request, form, formset, change):
        """Sauvegarder les formsets (incluant l'inline)."""
        if not change:  # Si c'est une création d'utilisateur
            # D'abord sauvegarder l'utilisateur
            form.save()
            # Ensuite créer le profil
            UserProfile.objects.get_or_create(user=form.instance)
        super().save_formset(request, form, formset, change)


# Réenregistrer avec notre admin étendu
admin.site.register(User, ExtendedUserAdmin)
