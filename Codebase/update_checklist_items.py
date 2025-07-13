import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgq_ligne_g.settings')
django.setup()

from wcm.models import ChecklistTemplate, ChecklistItem

# Supprimer les anciens items
ChecklistItem.objects.all().delete()

# Récupérer le template
template = ChecklistTemplate.objects.get(name="Check-list Production")

# Créer les nouveaux items plus courts
checklist_items = [
    ("Propreté machine", 1),
    ("Niveau huile", 2),
    ("Fuites", 3),
    ("Bandes transporteuses", 4),
    ("Arrêts d'urgence", 5),
    ("Température zones", 6),
    ("État rouleaux", 7),
    ("Aspiration", 8),
    ("Sécurités", 9),
    ("Éclairage", 10),
]

for text, order in checklist_items:
    ChecklistItem.objects.create(
        template=template,
        text=text,
        order=order
    )
    print(f"Créé : {text}")

print(f"\nCheck-list mise à jour avec {len(checklist_items)} items.")