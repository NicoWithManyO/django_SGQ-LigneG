#!/usr/bin/env python
"""Script pour mettre à jour les moyennes des postes existants."""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgq_ligne_g.settings')
django.setup()

from production.models import Shift

# Récupérer tous les postes
shifts = Shift.objects.all()
print(f"Mise à jour de {shifts.count()} postes...")

# Mettre à jour chaque poste
for i, shift in enumerate(shifts):
    print(f"\nPoste {i+1}/{shifts.count()}: {shift.shift_id}")
    
    # Calculer les moyennes
    shift.calculate_roll_averages()
    
    # Sauvegarder uniquement les champs des moyennes
    shift.save(update_fields=['avg_thickness_left_shift', 'avg_thickness_right_shift', 'avg_grammage_shift'])
    
    # Afficher les résultats
    print(f"  - Nb rouleaux: {shift.rolls.count()}")
    print(f"  - Moy. épaisseur G: {shift.avg_thickness_left_shift}")
    print(f"  - Moy. épaisseur D: {shift.avg_thickness_right_shift}")
    print(f"  - Grammage moyen: {shift.avg_grammage_shift}")

print("\nMise à jour terminée !")