import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgq_ligne_g.settings')
django.setup()

from production.models import Shift
from core.models import Operator
from datetime import date, time, timedelta

# Vérifier s'il y a des opérateurs
operators = Operator.objects.filter(is_active=True)
print(f"Nombre d'opérateurs actifs: {operators.count()}")

if operators.exists():
    operator = operators.first()
    print(f"Utilisation de l'opérateur: {operator.full_name}")
    
    # Créer un shift de test
    try:
        shift = Shift.objects.create(
            date=date.today(),
            operator=operator,
            vacation='Matin',
            start_time=time(6, 0),
            end_time=time(14, 0),
            availability_time=timedelta(hours=8),
            lost_time=timedelta(hours=0)
        )
        print(f"Shift créé avec succès! ID: {shift.id}, shift_id: {shift.shift_id}")
    except Exception as e:
        print(f"Erreur lors de la création du shift: {e}")
        import traceback
        traceback.print_exc()
else:
    print("Aucun opérateur actif trouvé!")
    
# Afficher tous les shifts
print(f"\nNombre total de shifts: {Shift.objects.count()}")