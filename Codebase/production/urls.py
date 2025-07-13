from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [
    path('', views.prod, name='prod'),
    # Toutes les autres URLs sont commentées - à refaire proprement
]