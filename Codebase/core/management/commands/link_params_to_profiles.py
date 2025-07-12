from django.core.management.base import BaseCommand
from core.models import Profile
from production.models import MachineParameters


class Command(BaseCommand):
    help = 'Lie automatiquement les paramètres machine aux profils correspondants'
    
    def handle(self, *args, **options):
        # Mapping des noms
        mappings = [
            ('40g/m²', '40gr/m²'),
            ('80g/m²', '80gr/m²'),
        ]
        
        for profile_name, params_name in mappings:
            try:
                profile = Profile.objects.get(name=profile_name)
                params = MachineParameters.objects.get(name=params_name)
                
                if not profile.machine_parameters:
                    profile.machine_parameters = params
                    profile.save()
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Lié "{params_name}" au profil "{profile_name}"'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'! Le profil "{profile_name}" a déjà des paramètres: {profile.machine_parameters.name}'
                    ))
                    
            except Profile.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'✗ Profil "{profile_name}" non trouvé'))
            except MachineParameters.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'✗ Paramètres "{params_name}" non trouvés'))
        
        self.stdout.write(self.style.SUCCESS('\nLiaison terminée!'))