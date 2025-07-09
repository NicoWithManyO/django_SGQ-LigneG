# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quality', '0006_thicknessspecification_max_nok'),
    ]

    operations = [
        migrations.AddField(
            model_name='thicknessspecification',
            name='name',
            field=models.CharField(default='80gr/m²', help_text='Ex: 80gr/m², 40gr/m²', max_length=50, unique=True, verbose_name='Nom'),
            preserve_default=False,
        ),
    ]