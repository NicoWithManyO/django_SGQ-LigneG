import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgq_ligne_g.settings')
django.setup()

from wcm.models import ChecklistTemplate, ChecklistItem

# Créer le template de check-list s'il n'existe pas
template, created = ChecklistTemplate.objects.get_or_create(
    name="Check-list Production",
    defaults={'description': 'Check-list standard pour la production'}
)

# Créer les items de check-list
checklist_items = [
    ("Vérifier l'état de propreté de la machine", 1),
    ("Contrôler le niveau d'huile", 2),
    ("Vérifier l'absence de fuite", 3),
    ("Contrôler l'état des bandes transporteuses", 4),
    ("Vérifier le bon fonctionnement des arrêts d'urgence", 5),
    ("Contrôler la température des zones de chauffe", 6),
    ("Vérifier l'état des rouleaux", 7),
    ("Contrôler le système d'aspiration", 8),
    ("Vérifier les dispositifs de sécurité", 9),
    ("Contrôler l'éclairage de la zone de travail", 10),
]

for text, order in checklist_items:
    ChecklistItem.objects.get_or_create(
        template=template,
        text=text,
        defaults={'order': order}
    )
    print(f"Créé : {text}")

print(f"\nCheck-list '{template.name}' créée avec {len(checklist_items)} items.")