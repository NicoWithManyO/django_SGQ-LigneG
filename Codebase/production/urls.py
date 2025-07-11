from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [
    path('', views.prod, name='prod'),
    path('shift/', views.shift_block, name='shift_create'),
    path('shift/<int:shift_id>/', views.shift_block, name='shift_edit'),
    path('shift/<int:shift_id>/save-field/', views.shift_save_field, name='shift_save_field'),
    
    # Auto-sauvegarde
    path('auto-save/', views.auto_save_form, name='auto_save_form'),
    path('get-saved-data/', views.get_saved_form_data, name='get_saved_form_data'),
    path('clear-saved-data/', views.clear_saved_form_data, name='clear_saved_form_data'),
    
    # Vérification rouleau
    path('check-roll-id/', views.check_roll_id, name='check_roll_id'),
    
    # Vérification shift
    path('check-shift-exists/', views.check_shift_exists, name='check_shift_exists'),
    
    # Gestion des opérateurs
    path('operator/create/', views.operator_create, name='operator_create'),
    
    # Contrôles qualité
    path('quality-controls/save/', views.save_quality_controls, name='save_quality_controls'),
    
    # Sauvegarde rouleau
    path('roll/save/', views.save_roll, name='save_roll'),
    
    # Temps d'arrêt
    path('shift/<int:shift_id>/lost-times/', views.get_shift_lost_times, name='get_shift_lost_times'),
    
    # Récupérer le dernier métrage
    path('get-last-meter-reading/', views.get_last_meter_reading, name='get_last_meter_reading'),
]