from django.urls import path
from . import views, views_quality

app_name = 'livesession'

urlpatterns = [
    path('update-field/', views.update_field, name='update_field'),
    path('get-active-roll/', views.get_active_roll, name='get_active_roll'),
    path('save-active-roll/', views.save_active_roll, name='save_active_roll'),
    path('auto-save/', views.auto_save_shift, name='auto_save_shift'),
    path('get-saved-data/', views.get_saved_data, name='get_saved_data'),
    path('clear-saved-data/', views.clear_saved_data, name='clear_saved_data'),
    
    # Contrôles qualité
    path('save-quality-control/', views_quality.save_quality_control, name='save_quality_control'),
    path('get-quality-control/', views_quality.get_quality_control, name='get_quality_control'),
]