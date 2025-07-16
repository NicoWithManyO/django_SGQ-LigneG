import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgq_ligne_g.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Créer le superuser
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("Superuser créé : username='admin', password='admin'")
else:
    print("Superuser 'admin' existe déjà")