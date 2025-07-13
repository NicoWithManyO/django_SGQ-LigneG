from django.urls import path
from . import views

app_name = 'quality'

urlpatterns = [
    path('defect-types/', views.get_defect_types, name='get_defect_types'),
    path('specifications/', views.get_all_specifications, name='get_all_specifications'),
    path('get-thickness-specs/', views.get_thickness_specifications, name='get_thickness_specifications'),
]