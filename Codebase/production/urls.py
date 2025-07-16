from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [
    path('', views.prod, name='prod'),
    path('profile/<int:profile_id>/parameters/', views.get_profile_parameters, name='get_profile_parameters'),
    # Toutes les autres URLs sont commentées - à refaire proprement
]