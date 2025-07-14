from django.urls import path
from . import api

app_name = 'livesession'

urlpatterns = [
    # API DRF unifiée
    path('api/current-session/', api.current_session, name='current_session'),
    path('api/current-session/save-shift/', api.save_shift, name='save_shift'),
]