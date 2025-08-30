from django.apps import AppConfig


class ProductionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'production'
    
    def ready(self):
        """Charge les signaux au démarrage de l'application."""
        # Temporairement désactivé pour debug de l'erreur 400
        # import production.signals
        pass
