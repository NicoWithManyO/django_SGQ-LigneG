from django.urls import path
from . import views

app_name = 'exporting'

urlpatterns = [
    path('api/export/rolls/download/', views.download_rolls_export, name='download_rolls'),
    path('api/export/rolls/status/', views.export_status, name='export_status'),
]