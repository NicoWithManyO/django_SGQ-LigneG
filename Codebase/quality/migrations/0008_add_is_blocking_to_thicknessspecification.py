# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quality', '0007_add_name_to_thicknessspecification'),
    ]

    operations = [
        migrations.AddField(
            model_name='thicknessspecification',
            name='is_blocking',
            field=models.BooleanField(default=True, help_text='Le non-respect de cette spec rend le rouleau non conforme', verbose_name='Bloquant'),
        ),
    ]