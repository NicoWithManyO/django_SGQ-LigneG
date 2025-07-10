# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0016_remove_roll_is_conform_roll_destination_roll_status'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='QualityControlSeries',
            new_name='QualityControl',
        ),
        migrations.AlterModelOptions(
            name='qualitycontrol',
            options={'ordering': ['-created_at'], 'verbose_name': 'Contrôle qualité', 'verbose_name_plural': 'Contrôles qualité'},
        ),
    ]