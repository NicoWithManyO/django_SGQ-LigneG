from django.core.management.base import BaseCommand
from core.models import MoodCounter


class Command(BaseCommand):
    help = 'Crée les 4 compteurs d\'humeur fixes'

    def handle(self, *args, **options):
        # S'assurer que tous les compteurs existent
        MoodCounter.ensure_all_moods_exist()
        
        # Afficher l'état actuel
        self.stdout.write(self.style.SUCCESS('Compteurs d\'humeur créés/vérifiés:'))
        
        for counter in MoodCounter.objects.all():
            self.stdout.write(f"  - {counter}")
        
        # Afficher les pourcentages
        self.stdout.write('\nPourcentages actuels:')
        percentages = MoodCounter.get_percentages()
        for mood, percentage in percentages.items():
            self.stdout.write(f"  - {mood}: {percentage}%")