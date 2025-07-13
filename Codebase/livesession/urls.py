from django.urls import path
from . import views

app_name = 'livesession'

urlpatterns = [
    path('update-field/', views.update_field, name='update_field'),
    path('get-active-roll/', views.get_active_roll, name='get_active_roll'),
    path('save-active-roll/', views.save_active_roll, name='save_active_roll'),
    path('auto-save/', views.auto_save_shift, name='auto_save_shift'),
    path('get-saved-data/', views.get_saved_data, name='get_saved_data'),
    path('clear-saved-data/', views.clear_saved_data, name='clear_saved_data'),
]