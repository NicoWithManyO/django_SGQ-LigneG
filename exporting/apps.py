from django.apps import AppConfig


class ExportingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'exporting'
    verbose_name = 'Export de données'
    
    def ready(self):
        """Enregistrer les signaux au démarrage de l'app."""
        import exporting.signals
