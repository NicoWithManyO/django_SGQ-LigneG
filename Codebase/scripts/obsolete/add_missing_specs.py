import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgq_ligne_g.settings')
django.setup()

from quality.models import Specification
from core.models import Profile

# Récupérer le profil
profile = Profile.objects.get(name='80gr/m²')

# Récupérer les spécifications manquantes
missing_specs = Specification.objects.filter(
    name='80gr/m²', 
    spec_type__in=['global_surface_mass', 'thickness']
)

print(f"Spécifications manquantes trouvées: {missing_specs.count()}")

for spec in missing_specs:
    profile.specifications.add(spec)
    print(f"  + Ajouté: {spec.name} ({spec.get_spec_type_display()})")

print(f"\nTotal des spécifications du profil: {profile.specifications.count()}")