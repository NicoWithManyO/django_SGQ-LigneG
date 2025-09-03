#!/usr/bin/env python3
"""
Script SIMPLE qui génère des données REELLES avec les opérateurs de la BDD
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgq_ligne_g.settings')
django.setup()

from production.models import Shift, Roll
from planification.models import Operator, FabricationOrder

def main():
    print("🔥 GENERATION SIMPLE DE DONNEES REELLES")
    
    # 1. UTILISER LES VRAIS OPERATEURS
    real_operators = list(Operator.objects.filter(is_active=True))
    if not real_operators:
        print("❌ AUCUN OPERATEUR TROUVE !")
        return
    
    print(f"✅ {len(real_operators)} opérateurs trouvés:")
    for op in real_operators:
        print(f"   - {op.employee_id}")
    
    # 2. CREER L'OF 5555
    of_5555, created = FabricationOrder.objects.get_or_create(
        order_number='5555',
        defaults={'target_length': 1200, 'is_active': True}
    )
    print(f"✅ OF 5555: {'créé' if created else 'existe déjà'}")
    
    # 3. GENERER 10 POSTES AVEC CES VRAIS OPERATEURS
    vacations = ['Matin', 'ApresMidi', 'Nuit']
    total_rolls = 0
    
    for i in range(10):
        # Date des derniers jours
        date = (datetime.now().date() - timedelta(days=i))
        
        # Opérateur au hasard parmi les vrais
        operator = random.choice(real_operators)
        vacation = random.choice(vacations)
        
        # Créer le poste
        shift = Shift.objects.create(
            date=date,
            operator=operator,
            vacation=vacation
        )
        
        print(f"✅ Poste créé: {shift.shift_id}")
        
        # Créer 3-6 rouleaux pour ce poste
        num_rolls = random.randint(3, 6)
        for j in range(num_rolls):
            Roll.objects.create(
                shift=shift,
                fabrication_order=of_5555,
                roll_number=total_rolls + 1,
                length=Decimal(str(random.uniform(80, 180))),
                tube_mass=Decimal(str(random.uniform(600, 800))),
                total_mass=Decimal(str(random.uniform(10000, 15000))),
                status='CONFORME' if random.random() > 0.1 else 'NON_CONFORME'
            )
            total_rolls += 1
        
        print(f"   → {num_rolls} rouleaux créés")
    
    print(f"\n🎉 TERMINE ! {total_rolls} rouleaux créés avec de VRAIS opérateurs !")

if __name__ == '__main__':
    main()