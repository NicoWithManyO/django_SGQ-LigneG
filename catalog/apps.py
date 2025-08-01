from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'catalog'
    
    def ready(self):
        """Import des signaux au démarrage de l'app."""
        import catalog.signals