# Generated manually
from django.db import migrations


def migrate_thickness_specs_to_specifications(apps, schema_editor):
    """Migre les données de ThicknessSpecification vers Specification."""
    ThicknessSpecification = apps.get_model('quality', 'ThicknessSpecification')
    Specification = apps.get_model('quality', 'Specification')
    
    for thickness_spec in ThicknessSpecification.objects.all():
        Specification.objects.create(
            spec_type='thickness',
            name=thickness_spec.name,
            value_min=thickness_spec.ep_mini,
            value_min_alert=thickness_spec.ep_mini_alerte,
            value_nominal=thickness_spec.ep_nominale,
            value_max_alert=thickness_spec.ep_max_alerte,
            value_max=None,  # Pas de max dans l'ancien modèle
            unit='mm',
            max_nok=thickness_spec.max_nok,
            is_blocking=thickness_spec.is_blocking,
            is_active=thickness_spec.is_active,
            comments=thickness_spec.comments,
            created_at=thickness_spec.created_at,
            updated_at=thickness_spec.updated_at,
        )


def reverse_migration(apps, schema_editor):
    """Reverse: supprime les specs de type thickness."""
    Specification = apps.get_model('quality', 'Specification')
    Specification.objects.filter(spec_type='thickness').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('quality', '0009_create_specification_model'),
    ]

    operations = [
        migrations.RunPython(
            migrate_thickness_specs_to_specifications,
            reverse_migration
        ),
    ]