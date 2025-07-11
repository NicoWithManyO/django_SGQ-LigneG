from django.urls import path
from . import views

app_name = 'quality'

urlpatterns = [
    path('get-thickness-specs/', views.get_thickness_specifications, name='get_thickness_specs'),
    # path('save-roll-defects/', views.save_roll_defects, name='save_roll_defects'),  # SUPPRIMÉ : Les défauts seront sauvegardés avec le rouleau
    path('get-all-specifications/', views.get_all_specifications, name='get_all_specifications'),
]