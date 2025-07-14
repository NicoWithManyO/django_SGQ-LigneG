"""
Filtres personnalisés pour l'admin Django avec comptage
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class CountedFilter(admin.SimpleListFilter):
    """
    Classe de base pour les filtres avec comptage
    """
    def lookups(self, request, model_admin):
        """
        Doit être implémenté par les sous-classes
        Retourne une liste de tuples (value, display_with_count)
        """
        raise NotImplementedError
    
    def queryset(self, request, queryset):
        """
        Doit être implémenté par les sous-classes
        """
        raise NotImplementedError


class RelatedCountedFilter(admin.RelatedFieldListFilter):
    """
    Version étendue de RelatedFieldListFilter qui affiche le nombre d'éléments
    """
    def field_choices(self, field, request, model_admin):
        """
        Surcharge pour ajouter le comptage aux choix
        """
        queryset = model_admin.get_queryset(request)
        
        # Obtenir les choix normaux
        choices = []
        for obj in field.related_model.objects.all():
            # Compter les objets qui ont cette valeur
            count = queryset.filter(**{field.name: obj.pk}).count()
            if count > 0:  # N'afficher que les choix qui ont des résultats
                choices.append((obj.pk, f"{str(obj)} ({count})"))
        
        return choices


class BooleanCountedFilter(admin.FieldListFilter):
    """
    Filtre booléen avec comptage
    """
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg = field_path
        self.lookup_val = params.get(self.lookup_kwarg)
        super().__init__(field, request, params, model, model_admin, field_path)
        
    def expected_parameters(self):
        return [self.lookup_kwarg]
    
    def choices(self, changelist):
        queryset = changelist.get_queryset(self.request)
        
        # Compter pour chaque valeur
        true_count = queryset.filter(**{self.lookup_kwarg: True}).count()
        false_count = queryset.filter(**{self.lookup_kwarg: False}).count()
        
        yield {
            'selected': self.lookup_val is None,
            'query_string': changelist.get_query_string(remove=[self.lookup_kwarg]),
            'display': _('All'),
        }
        yield {
            'selected': self.lookup_val == 'true',
            'query_string': changelist.get_query_string({self.lookup_kwarg: 'true'}),
            'display': f'Oui ({true_count})',
        }
        yield {
            'selected': self.lookup_val == 'false', 
            'query_string': changelist.get_query_string({self.lookup_kwarg: 'false'}),
            'display': f'Non ({false_count})',
        }
    
    def queryset(self, request, queryset):
        if self.lookup_val == 'true':
            return queryset.filter(**{self.lookup_kwarg: True})
        elif self.lookup_val == 'false':
            return queryset.filter(**{self.lookup_kwarg: False})
        return queryset


class ChoiceCountedFilter(admin.ChoicesFieldListFilter):
    """
    Filtre pour les champs avec choices qui affiche le comptage
    """
    def choices(self, changelist):
        queryset = changelist.get_queryset(self.request)
        
        yield {
            'selected': self.lookup_val is None,
            'query_string': changelist.get_query_string(remove=[self.lookup_kwarg]),
            'display': _('All'),
        }
        
        # Pour chaque choix possible
        for lookup, title in self.field.choices:
            count = queryset.filter(**{self.lookup_kwarg: lookup}).count()
            if count > 0:  # N'afficher que les choix qui ont des résultats
                yield {
                    'selected': str(lookup) == self.lookup_val,
                    'query_string': changelist.get_query_string({self.lookup_kwarg: lookup}),
                    'display': f'{title} ({count})',
                }