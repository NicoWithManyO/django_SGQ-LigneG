from django.urls import path
from . import api

app_name = 'livesession'

urlpatterns = [
    # API DRF unifiée
    path('api/current-session/', api.current_session, name='current_session'),
    path('api/current-session/save-shift/', api.save_shift, name='save_session'),
    path('api/save-roll/', api.save_roll, name='save_roll'),
    path('api/check-shift-id/<str:shift_id>/', api.check_shift_id, name='check_shift_id'),
    path('api/check-roll-id/<str:roll_id>/', api.check_roll_id, name='check_roll_id'),
    path('api/increment-mood/', api.increment_mood, name='increment_mood'),
    path('api/clear-production-data/', api.clear_production_data, name='clear_production_data'),
]