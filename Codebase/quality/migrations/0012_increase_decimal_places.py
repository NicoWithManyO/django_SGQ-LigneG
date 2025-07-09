# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quality', '0011_create_default_specs_and_remove_old_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='specification',
            name='value_max',
            field=models.DecimalField(blank=True, decimal_places=6, help_text='Seuil maximum critique', max_digits=12, null=True, verbose_name='Valeur maximale'),
        ),
        migrations.AlterField(
            model_name='specification',
            name='value_max_alert',
            field=models.DecimalField(blank=True, decimal_places=6, help_text="Seuil d'alerte maximum", max_digits=12, null=True, verbose_name='Valeur maximale alerte'),
        ),
        migrations.AlterField(
            model_name='specification',
            name='value_min',
            field=models.DecimalField(blank=True, decimal_places=6, help_text='Seuil minimum critique', max_digits=12, null=True, verbose_name='Valeur minimale'),
        ),
        migrations.AlterField(
            model_name='specification',
            name='value_min_alert',
            field=models.DecimalField(blank=True, decimal_places=6, help_text="Seuil d'alerte minimum", max_digits=12, null=True, verbose_name='Valeur minimale alerte'),
        ),
        migrations.AlterField(
            model_name='specification',
            name='value_nominal',
            field=models.DecimalField(blank=True, decimal_places=6, help_text='Valeur cible standard', max_digits=12, null=True, verbose_name='Valeur nominale'),
        ),
    ]