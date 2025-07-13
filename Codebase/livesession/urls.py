from django.urls import path
from . import views

app_name = 'livesession'

urlpatterns = [
    path('update-field/', views.update_field, name='update_field'),
]