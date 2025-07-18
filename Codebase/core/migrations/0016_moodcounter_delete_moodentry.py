# Generated by Django 5.2.4 on 2025-07-14 16:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_moodentry'),
    ]

    operations = [
        migrations.CreateModel(
            name='MoodCounter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mood_type', models.CharField(choices=[('no_response', 'Sans réponse'), ('happy', 'Content'), ('unhappy', 'Pas content'), ('neutral', 'Neutre')], max_length=20, unique=True, verbose_name="Type d'humeur")),
                ('count', models.PositiveIntegerField(default=0, verbose_name='Nombre de fois sélectionnée')),
            ],
            options={
                'verbose_name': 'MoOOoOod',
                'verbose_name_plural': 'MoOOoOods',
                'ordering': ['mood_type'],
            },
        ),
        migrations.DeleteModel(
            name='MoodEntry',
        ),
    ]
