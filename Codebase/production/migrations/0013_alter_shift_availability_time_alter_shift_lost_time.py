# Generated by Django 5.2.4 on 2025-07-09 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0012_remove_qualitycontrolseries_comments_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shift',
            name='availability_time',
            field=models.DurationField(blank=True, help_text='Temps de disponibilité', null=True, verbose_name='Temps disponible'),
        ),
        migrations.AlterField(
            model_name='shift',
            name='lost_time',
            field=models.DurationField(blank=True, help_text='Temps perdu', null=True, verbose_name='Temps perdu'),
        ),
    ]
