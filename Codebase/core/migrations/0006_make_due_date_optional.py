# Generated by Django 5.2.4 on 2025-07-06 12:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_add_for_cutting_to_fabrication_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fabricationorder',
            name='due_date',
            field=models.DateField(blank=True, help_text="Date d'échéance (optionnelle)", null=True),
        ),
    ]
