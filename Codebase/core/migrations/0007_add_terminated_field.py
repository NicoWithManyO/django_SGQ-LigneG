# Generated manually for adding terminated field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_make_due_date_optional'),
    ]

    operations = [
        migrations.AddField(
            model_name='fabricationorder',
            name='terminated',
            field=models.BooleanField(default=False, verbose_name='Terminé', help_text='Indique si cet ordre de fabrication est terminé'),
        ),
    ]