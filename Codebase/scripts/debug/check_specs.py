import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgq_ligne_g.settings')
django.setup()

from quality.models import Specification
from core.models import Profile

# Vérifier toutes les spécifications
specs = Specification.objects.all()
print(f"Nombre total de spécifications: {specs.count()}")
print("\nListe des spécifications:")
for spec in specs:
    print(f"  - {spec.name} ({spec.get_spec_type_display()}) - Active: {spec.is_active}")

# Vérifier le profil 80gr/m²
profile = Profile.objects.filter(name='80gr/m²').first()
if profile:
    print(f"\n\nProfil '{profile.name}':")
    print(f"  - Spécifications associées: {profile.specifications.count()}")
    
    if profile.specifications.count() == 0:
        print("\n  Aucune spécification associée au profil!")
        print("  Association des spécifications actives...")
        
        # Associer toutes les spécifications actives au profil
        active_specs = Specification.objects.filter(is_active=True)
        for spec in active_specs:
            profile.specifications.add(spec)
            print(f"    + Associé: {spec.name}")
        
        profile.save()
        print(f"\n  Total après association: {profile.specifications.count()} spécifications")
    else:
        print("\n  Spécifications associées:")
        for spec in profile.specifications.all():
            print(f"    - {spec.name} ({spec.get_spec_type_display()})")