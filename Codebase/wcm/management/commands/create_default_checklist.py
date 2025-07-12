from django.core.management.base import BaseCommand
from wcm.models import ChecklistTemplate, ChecklistItem


class Command(BaseCommand):
    help = 'Crée le template de check-list par défaut'
    
    def handle(self, *args, **options):
        # Créer le template par défaut
        template, created = ChecklistTemplate.objects.get_or_create(
            name="Check-list standard",
            defaults={
                'description': "Check-list de fin de poste standard",
                'is_active': True,
                'is_default': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Template "{template.name}" créé'))
        else:
            self.stdout.write(self.style.WARNING(f'Template "{template.name}" existe déjà'))
        
        # Items de la check-list standard
        items = [
            (10, "Paramètres machine vérifiés", True),
            (20, "Contrôles qualité effectués", True),
            (30, "Nettoyage zone de travail", True),
            (40, "Consignes de sécurité respectées", True),
            (50, "Documentation à jour", True),
            (60, "Anomalies signalées", True),
        ]
        
        for order, text, is_required in items:
            item, created = ChecklistItem.objects.get_or_create(
                template=template,
                order=order,
                defaults={
                    'text': text,
                    'is_required': is_required,
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  - Item "{text}" créé'))
            else:
                self.stdout.write(self.style.WARNING(f'  - Item "{text}" existe déjà'))
        
        self.stdout.write(self.style.SUCCESS('Check-list par défaut configurée!'))