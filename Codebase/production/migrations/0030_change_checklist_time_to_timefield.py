# Generated by Django 5.2.4 on 2025-07-11 21:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0029_add_checklist_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shift',
            name='checklist_signed_time',
            field=models.TimeField(blank=True, null=True, verbose_name='Heure signature check-list'),
        ),
    ]
