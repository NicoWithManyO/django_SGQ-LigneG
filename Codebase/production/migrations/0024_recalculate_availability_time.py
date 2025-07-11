from django.db import migrations
from datetime import timedelta


def recalculate_availability_times(apps, schema_editor):
    """Recalcule le temps disponible pour tous les shifts existants."""
    Shift = apps.get_model('production', 'Shift')
    
    for shift in Shift.objects.all():
        if shift.start_time and shift.end_time:
            # Calculer le temps d'ouverture
            from datetime import datetime
            start_datetime = datetime.combine(shift.date, shift.start_time)
            end_datetime = datetime.combine(shift.date, shift.end_time)
            
            # Si l'heure de fin est avant l'heure de début, c'est que le poste passe minuit
            if end_datetime < start_datetime:
                end_datetime += timedelta(days=1)
            
            opening_time = end_datetime - start_datetime
            
            # Temps disponible = Temps d'ouverture - Temps perdu
            if shift.lost_time:
                shift.availability_time = opening_time - shift.lost_time
            else:
                shift.availability_time = opening_time
            
            shift.save(update_fields=['availability_time'])


def reverse_func(apps, schema_editor):
    """Reverse: remet les temps disponibles égaux aux temps d'ouverture."""
    pass  # Pas de reverse nécessaire


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0023_recalculate_lost_times'),
    ]

    operations = [
        migrations.RunPython(recalculate_availability_times, reverse_func),
    ]