import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgq_ligne_g.settings')
django.setup()

from production.models import MachineParameters

# Mettre à jour les paramètres existants
params = MachineParameters.objects.get(name='80gr/m²')

# Ajouter des valeurs pour tous les paramètres
params.oxygen_primary = 180
params.oxygen_secondary = 50
params.propane_primary = 35
params.propane_secondary = 10
params.speed_primary = 1800
params.speed_secondary = 850
params.cage_speed = 1800
params.fiberizer_position = 85
params.tunnel_temperature = 280
params.polymerization_temperature = 180
params.mat_temperature = 160

params.save()

print(f"Paramètres mis à jour pour: {params.name}")
print(f"  - Oxygène primaire: {params.oxygen_primary}")
print(f"  - Oxygène secondaire: {params.oxygen_secondary}")
print(f"  - Propane primaire: {params.propane_primary}")
print(f"  - Propane secondaire: {params.propane_secondary}")
print(f"  - Vitesse primaire: {params.speed_primary}")
print(f"  - Vitesse secondaire: {params.speed_secondary}")
print(f"  - Vitesse cage: {params.cage_speed}")
print(f"  - Vitesse tapis: {params.belt_speed} Hz ({params.belt_speed_m_per_minute} m/min)")
print(f"  - Position fibrage: {params.fiberizer_position}")
print(f"  - Temp. tunnel: {params.tunnel_temperature}°C")
print(f"  - Temp. polymérisation: {params.polymerization_temperature}°C")
print(f"  - Temp. matelas: {params.mat_temperature}°C")