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
]