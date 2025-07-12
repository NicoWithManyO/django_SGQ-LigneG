from django.core.management.base import BaseCommand
from core.models import Profile
from production.models import MachineParameters


class Command(BaseCommand):
    help = 'Vérifie les profils et leurs paramètres machine'
    
    def handle(self, *args, **options):
        # Lister tous les profils
        self.stdout.write('\n=== PROFILS ===')
        for profile in Profile.objects.all():
            self.stdout.write(f'\nProfil: {profile.name} (ID: {profile.id})')
            self.stdout.write(f'  - Actif: {"Oui" if profile.is_active else "Non"}')
            self.stdout.write(f'  - Par défaut: {"Oui" if profile.is_default else "Non"}')
            self.stdout.write(f'  - Paramètres machine: {profile.machine_parameters.name if profile.machine_parameters else "AUCUN"}')
        
        # Lister tous les paramètres machine
        self.stdout.write('\n\n=== PARAMÈTRES MACHINE ===')
        for params in MachineParameters.objects.all():
            self.stdout.write(f'\nParamètres: {params.name} (ID: {params.id})')
            self.stdout.write(f'  - Actif: {"Oui" if params.is_active else "Non"}')
            profiles_using = params.profiles.all()
            if profiles_using:
                self.stdout.write(f'  - Utilisé par: {", ".join([p.name for p in profiles_using])}')
            else:
                self.stdout.write('  - Utilisé par: AUCUN PROFIL')