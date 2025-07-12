from django.core.management.base import BaseCommand
from core.models import Profile
from production.models import MachineParameters
from quality.models import Specification


class Command(BaseCommand):
    help = 'Crée les profils de production par défaut'
    
    def handle(self, *args, **options):
        # Créer les profils
        profiles_data = [
            {'name': '80g/m²', 'is_default': True},
            {'name': '40g/m²', 'is_default': False},
        ]
        
        for data in profiles_data:
            profile, created = Profile.objects.get_or_create(
                name=data['name'],
                defaults={
                    'is_active': True,
                    'is_default': data['is_default']
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Profil "{profile.name}" créé'))
                
                # Essayer de lier les paramètres machine existants
                try:
                    params = MachineParameters.objects.get(name=data['name'])
                    profile.machine_parameters = params
                    profile.save()
                    self.stdout.write(self.style.SUCCESS(f'  - Paramètres machine "{params.name}" liés'))
                except MachineParameters.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'  - Aucun paramètre machine trouvé pour "{data["name"]}"'))
                
                # Lier les spécifications correspondantes
                specs = Specification.objects.filter(name=data['name'], is_active=True)
                if specs.exists():
                    profile.specifications.set(specs)
                    self.stdout.write(self.style.SUCCESS(f'  - {specs.count()} spécifications liées'))
                else:
                    self.stdout.write(self.style.WARNING(f'  - Aucune spécification trouvée pour "{data["name"]}"'))
            else:
                self.stdout.write(self.style.WARNING(f'Profil "{profile.name}" existe déjà'))
        
        self.stdout.write(self.style.SUCCESS('Profils par défaut configurés!'))