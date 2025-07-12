from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from .models import LostTimeEntry, Shift, RollThickness, Roll


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


@receiver([post_save, post_delete], sender=RollThickness)
def update_roll_thickness_averages(sender, instance, **kwargs):
    """Met à jour les moyennes d'épaisseur du rouleau quand une mesure est ajoutée/modifiée/supprimée."""
    if instance.roll:
        try:
            # Recalculer les moyennes d'épaisseur
            instance.roll.calculate_thickness_averages()
            # Sauvegarder uniquement les champs des moyennes
            instance.roll.save(update_fields=['avg_thickness_left', 'avg_thickness_right'])
        except Roll.DoesNotExist:
            # Le rouleau a été supprimé, ne rien faire
            pass


@receiver([post_save, post_delete], sender=Roll)
def update_shift_roll_averages(sender, instance, **kwargs):
    """Met à jour les moyennes d'épaisseur et grammage du shift quand un rouleau est modifié."""
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
            # Recalculer les moyennes du shift
            instance.shift.calculate_roll_averages()
            
            # Sauvegarder les changements
            instance.shift.save(update_fields=['avg_thickness_left_shift', 'avg_thickness_right_shift', 'avg_grammage_shift'])
        except Shift.DoesNotExist:
            # Le shift a été supprimé, ne rien faire
            pass