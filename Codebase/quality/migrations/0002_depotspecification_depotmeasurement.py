# Generated by Django 5.2.4 on 2025-07-06 22:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quality', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DepotSpecification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fabrication_order', models.CharField(max_length=50, unique=True, verbose_name='Ordre de fabrication')),
                ('depot_nominal', models.DecimalField(decimal_places=1, help_text='Valeur cible de dépôt', max_digits=6, verbose_name='Dépôt nominal (g/m²)')),
                ('depot_min', models.DecimalField(decimal_places=1, help_text='Seuil minimum acceptable', max_digits=6, verbose_name='Dépôt minimum (g/m²)')),
                ('depot_max', models.DecimalField(decimal_places=1, help_text='Seuil maximum acceptable', max_digits=6, verbose_name='Dépôt maximum (g/m²)')),
                ('tolerance_percent', models.DecimalField(blank=True, decimal_places=1, help_text='Tolérance en % du nominal (auto-calculé si vide)', max_digits=4, null=True, verbose_name='Tolérance (%)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.CharField(blank=True, max_length=50, verbose_name='Créé par')),
                ('comments', models.TextField(blank=True, verbose_name='Commentaires')),
            ],
            options={
                'verbose_name': 'Spécification de dépôt',
                'verbose_name_plural': 'Spécifications de dépôt',
                'ordering': ['-updated_at'],
                'indexes': [models.Index(fields=['fabrication_order'], name='quality_dep_fabrica_e0018f_idx'), models.Index(fields=['is_active'], name='quality_dep_is_acti_b72eec_idx')],
            },
        ),
        migrations.CreateModel(
            name='DepotMeasurement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('roll_id', models.CharField(help_text='Format: OF_NumRouleau', max_length=50, verbose_name='ID Rouleau')),
                ('meter_position', models.PositiveIntegerField(verbose_name='Position (mètre)')),
                ('measured_value', models.DecimalField(decimal_places=1, max_digits=6, verbose_name='Valeur mesurée (g/m²)')),
                ('is_within_specification', models.BooleanField(default=True, verbose_name='Dans les spécifications')),
                ('deviation_percent', models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Écart nominal (%)')),
                ('measured_at', models.DateTimeField(auto_now_add=True, verbose_name='Mesuré le')),
                ('measured_by', models.CharField(blank=True, max_length=50, verbose_name='Mesuré par')),
                ('comments', models.TextField(blank=True, verbose_name='Commentaires')),
                ('specification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='quality.depotspecification', verbose_name='Spécification')),
            ],
            options={
                'verbose_name': 'Mesure de dépôt',
                'verbose_name_plural': 'Mesures de dépôt',
                'ordering': ['roll_id', 'meter_position', '-measured_at'],
                'indexes': [models.Index(fields=['roll_id'], name='quality_dep_roll_id_94c906_idx'), models.Index(fields=['meter_position'], name='quality_dep_meter_p_616d8d_idx'), models.Index(fields=['is_within_specification'], name='quality_dep_is_with_044b9a_idx'), models.Index(fields=['measured_at'], name='quality_dep_measure_5020d3_idx')],
            },
        ),
    ]
