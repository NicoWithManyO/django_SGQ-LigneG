from django.urls import path
from . import views

app_name = 'livesession'

urlpatterns = [
    path('update-field/', views.update_field, name='update_field'),
    path('get-active-roll/', views.get_active_roll, name='get_active_roll'),
]