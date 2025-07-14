import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgq_ligne_g.settings')
django.setup()

from production.models import MachineParameters

# Vérifier s'il y a des paramètres machine
params = MachineParameters.objects.all()
print(f"Nombre de profils de paramètres machine: {params.count()}")

if params.exists():
    for param in params:
        print(f"\nProfil: {param.name}")
        print(f"  - Oxygène primaire: {param.oxygen_primary}")
        print(f"  - Vitesse tapis: {param.belt_speed}")
else:
    print("\nAucun profil de paramètres machine trouvé.")
    print("Création de profils exemples...")
    
    # Créer des profils exemples
    profiles = [
        {
            'name': 'Standard',
            'oxygen_primary': 180,
            'oxygen_secondary': 50,
            'propane_primary': 35,
            'propane_secondary': 10,
            'cage_speed': 1800,
            'belt_speed': 15.5,
            'fiberizer_position': 85,
            'tunnel_temperature': 280,
            'polymerization_temperature': 180,
            'mat_temperature': 160,
        },
        {
            'name': 'Haute vitesse',
            'oxygen_primary': 200,
            'oxygen_secondary': 60,
            'propane_primary': 40,
            'propane_secondary': 12,
            'cage_speed': 2000,
            'belt_speed': 18.0,
            'fiberizer_position': 90,
            'tunnel_temperature': 290,
            'polymerization_temperature': 185,
            'mat_temperature': 165,
        }
    ]
    
    for profile_data in profiles:
        MachineParameters.objects.create(**profile_data)
        print(f"  Créé: {profile_data['name']}")