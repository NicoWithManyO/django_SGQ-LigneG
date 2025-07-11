# Generated by Django 5.2.4 on 2025-07-10 18:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0018_update_thickness_measurement_points'),
    ]

    operations = [
        migrations.AddField(
            model_name='roll',
            name='session_key',
            field=models.CharField(blank=True, help_text='Clé de session pour lier au shift en cours', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='roll',
            name='destination',
            field=models.CharField(choices=[('PRODUCTION', 'Production'), ('DECOUPE', 'Découpe'), ('DECHETS', 'Déchets')], default='PRODUCTION', max_length=20, verbose_name='Destination'),
        ),
        migrations.AlterField(
            model_name='roll',
            name='shift',
            field=models.ForeignKey(blank=True, help_text='Poste associé (sera lié lors de la sauvegarde du poste)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rolls', to='production.shift', verbose_name='Poste de production'),
        ),
    ]
