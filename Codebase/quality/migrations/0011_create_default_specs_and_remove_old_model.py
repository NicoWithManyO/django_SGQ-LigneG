# Generated manually
from django.db import migrations


def create_default_specifications(apps, schema_editor):
    """Crée les spécifications par défaut pour chaque type."""
    Specification = apps.get_model('quality', 'Specification')
    
    # Créer les specs pour 80gr/m² si elles n'existent pas déjà
    specs_to_create = [
        {
            'spec_type': 'micrometer',
            'name': '80gr/m²',
            'unit': 'µm',
            'is_blocking': True,
            'is_active': True,
            'comments': 'Spécification micronnaire pour 80gr/m²'
        },
        {
            'spec_type': 'surface_mass',
            'name': '80gr/m²',
            'unit': 'g/m²',
            'is_blocking': True,
            'is_active': True,
            'comments': 'Spécification masse surfacique pour 80gr/m²'
        },
        {
            'spec_type': 'dry_extract',
            'name': '80gr/m²',
            'unit': '%',
            'is_blocking': False,
            'is_active': True,
            'comments': 'Spécification extrait sec pour 80gr/m²'
        }
    ]
    
    for spec_data in specs_to_create:
        # Vérifier si n'existe pas déjà
        if not Specification.objects.filter(
            spec_type=spec_data['spec_type'],
            name=spec_data['name']
        ).exists():
            Specification.objects.create(**spec_data)


def reverse_create_default_specifications(apps, schema_editor):
    """Supprime les specs créées."""
    Specification = apps.get_model('quality', 'Specification')
    Specification.objects.filter(
        spec_type__in=['micrometer', 'surface_mass', 'dry_extract'],
        name='80gr/m²'
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('quality', '0010_migrate_thickness_to_specification'),
    ]

    operations = [
        # D'abord créer les specs par défaut
        migrations.RunPython(
            create_default_specifications,
            reverse_create_default_specifications
        ),
        
        # Ensuite supprimer l'ancien modèle ThicknessSpecification
        migrations.DeleteModel(
            name='ThicknessSpecification',
        ),
    ]