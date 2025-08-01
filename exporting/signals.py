from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from production.models import Roll
from .services import RollExcelExporter
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Roll)
def export_roll_to_excel(sender, instance, created, **kwargs):
    """Signal pour exporter automatiquement chaque rouleau sauvegardé."""
    # Exporter les nouveaux rouleaux et les mises à jour
    try:
        exporter = RollExcelExporter()
        # Pour les mises à jour, on utilise update=True (défaut)
        # Pour les créations, on pourrait forcer update=False mais ce n'est pas nécessaire
        success, result = exporter.export_roll(instance, update=True)
        
        if success:
            action = "créé et exporté" if created else "mis à jour"
            logger.info(f"Rouleau {instance.roll_id} {action} dans {result}")
        else:
            logger.error(f"Erreur export rouleau {instance.roll_id}: {result}")
            
    except Exception as e:
        logger.error(f"Erreur signal export rouleau {instance.roll_id}: {str(e)}")


@receiver(pre_delete, sender=Roll)
def delete_roll_from_excel(sender, instance, **kwargs):
    """Signal pour supprimer automatiquement un rouleau de l'Excel."""
    try:
        exporter = RollExcelExporter()
        success, result = exporter.delete_roll(instance)
        
        if success:
            logger.info(f"Rouleau {instance.roll_id} supprimé de {result}")
        else:
            logger.error(f"Erreur suppression rouleau {instance.roll_id}: {result}")
            
    except Exception as e:
        logger.error(f"Erreur signal suppression rouleau {instance.roll_id}: {str(e)}")