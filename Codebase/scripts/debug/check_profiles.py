import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgq_ligne_g.settings')
django.setup()

from core.models import Profile
from production.models import MachineParameters

# Vérifier les profils
profiles = Profile.objects.all()
print(f"Nombre de profils: {profiles.count()}")

for profile in profiles:
    print(f"\nProfil: {profile.name}")
    print(f"  - Paramètres machine: {profile.machine_parameters}")
    print(f"  - Actif: {profile.is_active}")
    print(f"  - Par défaut: {profile.is_default}")

# Vérifier le profil 80gr/m²
profile_80 = Profile.objects.filter(name='80gr/m²').first()
if profile_80:
    print(f"\n\nProfil 80gr/m² trouvé")
    if not profile_80.machine_parameters:
        print("Pas de paramètres machine associés. Association en cours...")
        
        # Chercher les paramètres machine 80gr/m²
        params = MachineParameters.objects.filter(name='80gr/m²').first()
        if params:
            profile_80.machine_parameters = params
            profile_80.save()
            print(f"Paramètres machine '{params.name}' associés au profil")
        else:
            print("Aucun paramètre machine '80gr/m²' trouvé")