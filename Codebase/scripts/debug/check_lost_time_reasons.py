#!/usr/bin/env python
import os
import sys
import django

# Ajouter le chemin du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SGQ_LigneG.settings')
django.setup()

from wcm.models import LostTimeReason

print("=== Vérification des motifs de temps perdu ===\n")

# Lister tous les motifs
reasons = LostTimeReason.objects.all().order_by('order', 'name')

if not reasons.exists():
    print("❌ Aucun motif de temps perdu trouvé !")
    print("\nVous devez créer des motifs dans l'admin ou utiliser un script d'initialisation.")
else:
    print(f"✅ {reasons.count()} motifs trouvés:\n")
    for reason in reasons:
        print(f"ID: {reason.id} | Code: {reason.code or 'N/A'} | Nom: {reason.name}")
        print(f"   Catégorie: {reason.category or 'N/A'} | Actif: {reason.is_active}")
        print(f"   Ordre: {reason.order} | Couleur: {reason.color}")
        if reason.description:
            print(f"   Description: {reason.description}")
        print()
    
    # Vérifier si "Démarrage machine" existe
    demarrage_motifs = reasons.filter(name__icontains='démarr')
    if demarrage_motifs.exists():
        print("\n✅ Motif(s) de démarrage trouvé(s):")
        for motif in demarrage_motifs:
            print(f"   - {motif.name} (ID: {motif.id})")
    else:
        print("\n⚠️  Aucun motif de démarrage trouvé (contenant 'démarr')")