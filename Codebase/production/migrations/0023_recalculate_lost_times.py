from django.db import migrations
from datetime import timedelta


def recalculate_lost_times(apps, schema_editor):
    """Recalcule le temps perdu pour tous les shifts existants."""
    Shift = apps.get_model('production', 'Shift')
    
    for shift in Shift.objects.all():
        # Calculer la somme des temps d'arrêt
        total_minutes = 0
        for lost_time in shift.lost_time_entries.all():
            total_minutes += lost_time.duration
        
        # Mettre à jour le champ lost_time
        shift.lost_time = timedelta(minutes=total_minutes)
        shift.save(update_fields=['lost_time'])


def reverse_func(apps, schema_editor):
    """Reverse: remet les temps perdus à zéro."""
    Shift = apps.get_model('production', 'Shift')
    Shift.objects.all().update(lost_time=timedelta(seconds=0))


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0022_update_lost_time_calculation'),
    ]

    operations = [
        migrations.RunPython(recalculate_lost_times, reverse_func),
    ]