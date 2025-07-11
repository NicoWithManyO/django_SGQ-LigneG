from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from .models import LostTimeEntry, Shift


@receiver([post_save, post_delete], sender=LostTimeEntry)
def update_shift_lost_time(sender, instance, **kwargs):
    """Met à jour le temps perdu total et le temps disponible du shift quand un temps d'arrêt est modifié."""
    # Ne pas exécuter si c'est un signal post_delete et que le shift est en cours de suppression
    if kwargs.get('signal') == post_delete:
        try:
            # Vérifier si le shift existe encore
            if instance.shift_id and not Shift.objects.filter(pk=instance.shift_id).exists():
                return
        except:
            return
    
    if instance.shift:
        try:
            # Recalculer le temps perdu
            instance.shift.lost_time = instance.shift.calculate_lost_time()
            
            # Recalculer le temps disponible si on a les heures de début/fin
            if instance.shift.start_time and instance.shift.end_time:
                instance.shift.availability_time = instance.shift.opening_time - instance.shift.lost_time
            
            # Sauvegarder les changements
            instance.shift.save(update_fields=['lost_time', 'availability_time'])
        except Shift.DoesNotExist:
            # Le shift a été supprimé, ne rien faire
            pass