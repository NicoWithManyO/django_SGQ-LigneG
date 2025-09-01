from django.urls import path
from . import views

app_name = 'exporting'

urlpatterns = [
    # Export des rouleaux
    path('api/export/rolls/download/', views.download_rolls_export, name='download_rolls'),
    path('api/export/rolls/status/', views.export_status, name='export_status'),
    
    # Export des shifts
    path('api/export/shifts/download/', views.download_shifts_export, name='download_shifts'),
    path('api/export/shifts/status/', views.shifts_export_status, name='shifts_export_status'),
]