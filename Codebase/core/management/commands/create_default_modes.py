from django.core.management.base import BaseCommand
from core.models import Mode


class Command(BaseCommand):
    help = 'Crée les modes de fonctionnement par défaut'
    
    def handle(self, *args, **options):
        # Définir les modes par défaut
        modes_data = [
            {
                'name': 'Permissif',
                'code': 'permissive',
                'description': 'Mode permissif : permet certaines tolérances sur les contrôles et validations',
                'is_enabled': False
            },
            {
                'name': 'Dégradé',
                'code': 'degraded',
                'description': 'Mode dégradé : fonctionnement limité suite à un problème technique',
                'is_enabled': False
            },
            {
                'name': 'Maintenance',
                'code': 'maintenance',
                'description': 'Mode maintenance : pour les opérations de maintenance et tests',
                'is_enabled': False
            },
        ]
        
        for data in modes_data:
            mode, created = Mode.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'is_enabled': data['is_enabled'],
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Mode "{mode.name}" créé'))
            else:
                self.stdout.write(self.style.WARNING(f'Mode "{mode.name}" existe déjà'))
        
        self.stdout.write(self.style.SUCCESS('\nModes par défaut configurés!'))