# Temporairement désactivé pour debug de l'erreur 400
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import Roll


# @receiver(post_save, sender=Roll)
# def update_trs_on_roll_save(sender, instance, **kwargs):
#     """
#     Met à jour le TRS du shift quand un rouleau est modifié.
#     Les longueurs du shift sont recalculées automatiquement par les propriétés,
#     donc on doit juste recalculer le TRS.
#     """
#     if instance.shift:
#         # Recalculer le TRS car les longueurs ont potentiellement changé
#         from wcm.services import calculate_and_create_trs
#         try:
#             calculate_and_create_trs(instance.shift)
#         except Exception as e:
#             # Logger l'erreur mais ne pas faire échouer la sauvegarde
#             print(f"Erreur lors de la mise à jour du TRS: {e}")