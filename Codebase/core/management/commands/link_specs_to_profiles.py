from django.core.management.base import BaseCommand
from core.models import Profile
from quality.models import Specification


class Command(BaseCommand):
    help = 'Lie les spécifications existantes aux profils correspondants'
    
    def handle(self, *args, **options):
        # Pour chaque profil actif
        for profile in Profile.objects.filter(is_active=True):
            self.stdout.write(f'\nTraitement du profil "{profile.name}"...')
            
            # Chercher toutes les spécifications qui correspondent au nom du profil
            specs = Specification.objects.filter(name=profile.name, is_active=True)
            
            if specs.exists():
                # Lier les spécifications au profil
                profile.specifications.set(specs)
                
                # Afficher le détail
                self.stdout.write(self.style.SUCCESS(f'  - {specs.count()} spécifications liées:'))
                for spec in specs:
                    self.stdout.write(f'    • {spec.get_spec_type_display()} ({spec.name})')
            else:
                self.stdout.write(self.style.WARNING(f'  - Aucune spécification trouvée'))
        
        self.stdout.write(self.style.SUCCESS('\nLiaison des spécifications terminée!'))